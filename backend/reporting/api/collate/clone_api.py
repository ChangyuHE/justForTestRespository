import logging
from api.models import CloneJob, Validation
from .business_entities import CloneRequestDTO, CloneOutcomeBuilder
from .tasks.task_clone import do_clone

log = logging.getLogger(__name__)


def clone_validations(request_dto: CloneRequestDTO) -> CloneOutcomeBuilder:
    outcome = CloneOutcomeBuilder()

    # Sanity check
    _verify_request(request_dto, outcome)

    if not outcome.is_success():
        return outcome

    job = CloneJob.objects.create(
        requester=request_dto.requester,
        validation_name=request_dto.validation_name,
        notes=request_dto.notes,
        site_url=request_dto.site_url,
    )

    do_clone.send(job.id, request_dto.validation_id)
    outcome.job_id = job.id

    return outcome


def _verify_request(request_dto: CloneRequestDTO, outcome: CloneOutcomeBuilder):
    """ Checks if request contains valid data.
    """
    # Validation name should be provided
    if request_dto.validation_name_missed():
        outcome.add_validation_name_error()

    # validation should be selected for clone
    if not request_dto.validation_id:
        outcome.add_selected_validation_error()
        return

    # source validation should exists
    source_validation = Validation.objects.filter(pk=request_dto.validation_id).first()
    if not source_validation:
        outcome.add_nonexistent_validation_error()
        return

    # check if validation with the given parameters does not exists
    if outcome.is_success():
        query_filter = dict(
            name=request_dto.validation_name,
            env_id=source_validation.env_id,
            platform_id=source_validation.platform_id,
            os_id=source_validation.os_id
        )
        if Validation.objects.filter(**query_filter).exists():
            outcome.add_duplicated_validation_error()
