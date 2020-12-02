import logging

from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.db import transaction
from django.template.loader import get_template
from dramatiq import actor

from api.collate.utils.merge_clone import create_validation, copy_results, MODE
from api.models import JobStatus, Validation, CloneJob
from reporting.site_settings import production

log = logging.getLogger(__name__)


@actor
@transaction.atomic
def do_clone(job_id: int, validation_id: int):
    try:
        job = CloneJob.objects.get(pk=job_id)
        log.debug('Started clone task with id: %d, username: %s', job_id, job.requester.username)

        # Create new validation
        validation = create_validation(job, [validation_id], MODE.CLONE)

        # Flat copy results from validation list
        copy_results(validation, [validation_id], None)

        job.status = JobStatus.DONE

    except:
        log.exception('Clone job failed.')
        job.status = JobStatus.FAILED

    finally:
        job.save()

    _send_clone_notification(job, validation, validation_id)


def _send_clone_notification(job: CloneJob, validation: Validation, validation_id: int):
    cloned_validation = Validation.alive_objects.get(pk=validation_id)

    context = dict(
        site_url=job.site_url,
        validation_id=validation.id,
        validation_name=validation.name,
        cloned_val_id=cloned_validation.id,
        cloned_val_name=cloned_validation.name,
    )

    recipients = []
    if job.requester.email:
        recipients.append(job.requester.email)

    if job.status == JobStatus.DONE:
        template_name = 'collate/clone_success.html'
        subject = f"Reporter: Validation '{validation.name}' is cloned successfully"
        clone_status = 'cloned SUCCESSFULLY'
    else:
        template_name = 'collate/clone_failure.html'
        subject = f"Reporter: Clone of '{validation.name}' failed"
        recipients += get_user_model().staff_emails()
        clone_status = 'FAILED to clone'

    template = get_template(template_name)
    text = template.render(context)

    log.debug('Validation with id %d is %s, sending notification message.', validation_id, clone_status)
    log.debug('Subject of notification message: %s', subject)
    log.debug('Recipients: %s', recipients)

    if production:
        message = EmailMessage(subject, text, None, recipients)
        message.content_subtype = 'html'
        message.send()
