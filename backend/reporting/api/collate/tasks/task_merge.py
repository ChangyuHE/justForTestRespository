import logging

from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.db import transaction
from django.template.loader import get_template
from dramatiq import actor

from api.collate.utils.merge_clone import create_validation, copy_results, MODE
from api.models import JobStatus
from api.models import MergeJob
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
        validation = create_validation(job, validation_ids, MODE.MERGE)

        # Flat copy results from validation list
        copy_results(validation, validation_ids, job.strategy)

        job.status = JobStatus.DONE

    except:
        log.exception('Merge job failed.')
        job.status = JobStatus.FAILED

    finally:
        job.save()

    _send_merge_notification(job, validation, validation_ids)


def _send_merge_notification(job, validation, validation_ids):
    merged_validations = tuple(Validation.alive_objects.filter(pk__in=validation_ids)
                               .values_list('id', 'name'))

    context = dict(
        site_url=job.site_url,
        validation_id=validation.id,
        validation_name=validation.name,
        merged_validations=merged_validations,
    )

    recipients = []
    if job.requester.email:
        recipients.append(job.requester.email)

    if job.status == JobStatus.DONE:
        template_name = 'collate/merge_success.html'
        subject = 'Reporter: validations are merged successfully'
        merge_status = 'merged SUCCESSFULLY'
    else:
        template_name = 'collate/merge_failure.html'
        subject = 'Reporter: validations merge failed'
        recipients += get_user_model().staff_emails()
        merge_status = 'FAILED to merge'

    template = get_template(template_name)
    text = template.render(context)

    log.debug('Validations with ids %s are %s, sending notification message.', str(validation_ids), merge_status)
    log.debug('Subject of notification message: %s', subject)
    log.debug('Recipients: %s', recipients)

    if production:
        message = EmailMessage(subject, text, None, recipients)
        message.content_subtype = 'html'
        message.send()
