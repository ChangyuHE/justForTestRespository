import logging

from api.models import Os
from api.models import Env
from api.models import Platform
from api.models import Validation
from api.models import MergeJob

from .business_entities import MergeRequestDTO
from .business_entities import MergeOutcomeBuilder
from .tasks.task_merge import do_merge

log = logging.getLogger(__name__)


def merge_validations(request_dto: MergeRequestDTO) -> MergeOutcomeBuilder:
    outcome = MergeOutcomeBuilder()

    # Sanity check
    _verify_request(request_dto, outcome)

    # Check data consistance.
    _verify_consistence(request_dto, outcome)

    if not outcome.is_success():
        return outcome

    job = MergeJob.objects.create(
        requester=request_dto.requester,
        validation_name=request_dto.validation_name,
        notes=request_dto.notes,
        site_url=request_dto.site_url,
        strategy=request_dto.strategy,
    )

    do_merge.send(job.id, request_dto.validation_ids)
    outcome.job_id = job.id

    return outcome


def _verify_request(request_dto: MergeRequestDTO, outcome: MergeOutcomeBuilder):
    """ Checks if request contains valid data.
    """
    # Validation name should be provided
    if request_dto.validation_name_missed():
        outcome.add_validation_name_error()

    # At least two validations should be selected for merge
    if len(request_dto.validation_ids) < 2:
        outcome.add_validation_list_error()


def _verify_consistence(request_dto: MergeRequestDTO, outcome: MergeOutcomeBuilder):
    """ Ensures that results from all specified validations can be
        collected together as new single validation results.
    """

    if not outcome.is_success():
        return

    # Check validation constraints
    base_validation = Validation.alive_objects.get(pk=request_dto.validation_ids[0])
    query_filter = dict(
        name=request_dto.validation_name,
        env=base_validation.env,
        os=base_validation.os,
        platform=base_validation.platform,
    )

    if Validation.alive_objects.filter(**query_filter).count() > 0:
        message = 'Validation with such parameters already exists'
        outcome.add_existing_validation_error(message, query_filter.items())

    # Verify that os, env and platform columns contain only one distinct value.
    query_map = [
        (Os, 'Operating system'),
        (Env, 'Environment'),
        (Platform, 'Platform'),
    ]

    for model, name in query_map:
        values = model.objects.filter(
            result__validation__id__in=request_dto.validation_ids
        ).distinct().values_list('name', flat=True)

        if len(values) > 1:
            outcome.add_ambiguous_column_error(name, values)
