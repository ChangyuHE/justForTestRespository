import logging

from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.db import transaction
from django.template.loader import get_template
from dramatiq import actor
from typing import List

from api.models import JobStatus
from api.models import MergeJob
from api.models import Result
from api.models import Validation

from reporting.settings import production

log = logging.getLogger(__name__)


@actor
@transaction.atomic
def do_merge(job_id, validation_ids):
    try:
        job = MergeJob.objects.get(pk=job_id)
        log.debug('Started merge task with id: %s, username: %s', job_id, job.requester.username)

        # Create new validation
        validation = _create_validation(job, validation_ids)

        # Flat copy results from validation list
        _copy_results(validation, validation_ids, job.strategy)

        job.status = JobStatus.DONE

    except:
        log.exception('Merge job failed.')
        job.status = JobStatus.FAILED

    finally:
        job.save()

    _send_merge_notification(job, validation, validation_ids)

def _create_validation(job, validation_ids: List[int]) -> Validation:
    ''' Create new Validation entity for merged results.
    '''
    validation = Validation.objects.get(pk=validation_ids[0])
    validation.id = None
    validation.name = job.validation_name

    source_names = Validation.objects.filter(pk__in=validation_ids).values_list('name', flat=True)
    validation.notes = (
        'Merge of validations: '
        + ', '.join(source_names)
        + '\n\n'
        + job.notes
    )
    validation.save()

    return validation

def _copy_results(target_validation: Validation, validation_ids: List[int], strategy: str):
    ''' Copy all results from source validations into target validation.
        All validations must have the same Env, Os and Platform values.
        Merge strategy (best/last) should be provided by user.
    '''

    if strategy == 'last':
        strategy_args = ('-validation__date', '-id')
    else:
        strategy = 'best'
        strategy_args = ('-status__priority', '-validation__date', '-id')

    log.debug("Using '%s' strategy to merge validation results.", strategy)

    new_entities = []

    for entity in _query_result_distinct_on_item(validation_ids, strategy_args):
        entity.id = None
        entity.validation = target_validation
        new_entities.append(entity)

    Result.objects.bulk_create(new_entities)
    vstats = target_validation.update_status_counters()
    log.debug("Merged validation details - %s", vstats.__format__('full'))

def _query_result_distinct_on_item(validation_ids, strategy_args):
    unique_item_ids = []

    for entity in (Result.objects
            .filter(validation_id__in=validation_ids)
            .order_by('item_id', *strategy_args)):
        if entity.item_id not in unique_item_ids:
            unique_item_ids.append(entity.item_id)
            yield entity

def _send_merge_notification(job, validation, validation_ids):
    merged_validations = tuple(Validation.objects.filter(pk__in=validation_ids)
            .values_list('id', 'name'))

    context = dict(
        job_id = job.id,
        site_url = job.site_url,
        validation_id = validation.id,
        validation_name = validation.name,
        merged_validations = merged_validations,
    )

    recipients = []
    if job.requester.email:
        recipients.append(job.requester.email)

    if job.status == JobStatus.DONE:
        template_name = 'collate/merge_success.html'
        subject = 'Reporter: validations merge success'
    else:
        template_name = 'collate/merge_failure.html'
        subject = 'Reporter: validations merge failure'
        recipients += get_user_model().staff_emails()

    template = get_template(template_name)
    text = template.render(context)

    log.debug('Validations with ids %s are merged, sending notification message.',
            str(validation_ids))

    if production:
        message = EmailMessage(subject, text, None, recipients)
        message.content_subtype = 'html'
        message.send()
