import logging
from enum import Enum
from typing import List

from django.db import transaction

from api.models import Validation, Result

log = logging.getLogger(__name__)


class MODE(Enum):
    MERGE = 'merge'
    CLONE = 'clone'


@transaction.atomic
def create_validation(job, validation_ids: List[int], mode: MODE) -> Validation:
    """ Create new Validation entity for merged or cloned results.
    """
    validation = Validation.objects.get(pk=validation_ids[0])
    validation.id = None
    validation.name = job.validation_name

    source_names = Validation.objects.filter(pk__in=validation_ids).values_list('name', flat=True)
    validation.notes = (
        ('Merge of validations: ' if mode == MODE.MERGE else 'Clone of validation: ')
        + ', '.join(source_names)
        + '\n\n'
        + job.notes if job.notes else ''
    )
    validation.save()

    return validation


def copy_results(target_validation: Validation, validation_ids: List[int], strategy: str):
    """ Copy all results from source validations into target validation.
        All validations must have the same Env, Os and Platform values.
        Merge strategy (best/last) should be provided by user.
    """

    new_entities = []

    for entity in _query_result_distinct_on_item(validation_ids, strategy):
        entity.id = None
        entity._changed = False
        entity.validation = target_validation
        new_entities.append(entity)

    Result.objects.bulk_create(new_entities)
    vstats = target_validation.update_status_counters()
    c_and_f = target_validation.update_components_and_features()

    log.debug(f"{'Merged' if strategy else 'Cloned'} validation details:")
    log.info('  Item statuses: %s', vstats.__format__('full'))
    log.info('  Components: %s', c_and_f.components_as_str())
    log.info('  Features: %s', c_and_f.features_as_str())


def _query_result_distinct_on_item(validation_ids, strategy):
    if strategy:
        if strategy == 'last':
            strategy_args = ('-validation__date', '-id')
        else:
            strategy = 'best'
            strategy_args = ('-status__priority', '-validation__date', '-id')

        log.debug("Using '%s' strategy to merge validation results.", strategy)
    else:
        strategy_args = []
    unique_item_ids = []

    for entity in (Result.objects.filter(validation_id__in=validation_ids).order_by('item_id', *strategy_args)):
        if entity.item_id not in unique_item_ids:
            unique_item_ids.append(entity.item_id)
            yield entity
