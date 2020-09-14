import dataclasses
import logging
from pathlib import Path
from typing import Dict
import dramatiq
from django.template import Template
from django.template import Context as django_context

from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.db import transaction

from api.models import ImportJob
from api.collate.business_entities import Context
from api.collate.business_entities import ValidationDTO
from api.collate.excel_utils import open_excel_file
from api.collate.excel_utils import non_empty_row
from api.collate.services import RecordBuilder
from reporting.settings import production

log = logging.getLogger(__name__)


@dataclasses.dataclass
class Changes:
    added: int = 0
    updated: int = 0
    skipped: int = 0

    def update_from_entity(self, entity):
        if entity is None:
            self.skipped += 1
        elif entity.id is None:
            entity.save()
            self.added += 1
        else:
            entity.save()
            self.updated += 1


@dramatiq.actor
@transaction.atomic
def do_import(job_id: int, validation_dict: Dict, force_run: bool, site_url: str):
    to_emails = []
    validation_info = '<unknown>'

    try:
        job = ImportJob.objects.get(pk=job_id)
        log.debug("Started task: username=%s, table path: %s", job.requester.username, job.path)
        if job.requester.email:
            to_emails.append(job.requester.email)

        context = Context()
        outcome = context.outcome
        outcome.job_id = job_id
        dto = ValidationDTO(**validation_dict)
        validation = dto.to_validation()

        if validation is None:
            message = f'Job {job_id} failed: Validation with id {dto.id} does not exist.'
            log.error(message)
            outcome.add_invalid_validation_error(message)
            return

        validation_info = validation.name
        context.validation = validation
        context.save_transient_validation()

        # Load workbook
        workbook = open_excel_file(job.path, outcome)
        if workbook is None:
            return

        # Get necessary data from workbook
        context.mapping.set_from_workbook(workbook, outcome)
        changes = Changes()
        rows = context.mapping.sheet.rows
        next(rows)

        # Process file content row by row and perform queries to get additional data
        for row in non_empty_row(rows):
            builder = RecordBuilder(context, row)
            entity = builder.build(force_run)
            changes.update_from_entity(entity)

        outcome.changes = dataclasses.asdict(changes)

        log.debug('File store outcome: %s', outcome.build())
        # if not outcome.is_success():
        #     transaction.set_rollback(True)
    except Exception:
        log.exception("Import job failed")
        # Get list of staff e-mails to report an error
        to_emails += get_user_model().staff_emails()
        text = f'Import of validation <b>{validation_info}</b> failed.'
        topic = f'Reporter: import of validation {validation_info} failed'
        job.status = ImportJob.Status.FAILED
    else:
        template = Template("""
Import of validation <a href="{{ site_url }}validation/{{ validation_id }}">{{ validation_info }}</a> is done.<br>
Test items:
<ul>
    {% if added %}
        <li>added: {{ added }}</li>
    {% endif %}
    {% if updated %}
        <li>updated: {{ updated }}</li>
    {% endif %}
    {% if skipped %}
        <li>skipped: {{ skipped }}</li>
    {% endif %}
</ul>
""")
        context = django_context({'validation_info': validation_info,
                           'added': changes.added,
                           'updated': changes.updated,
                           'skipped': changes.skipped,
                           'site_url': site_url,
                           'validation_id': context.get_validation_id()})
        text = template.render(context)
        topic = f'Reporter: import of validation {validation_info}'
        job.status = ImportJob.Status.DONE
    finally:
        if production:
            log.info("Sending an e-mail...")
            msg = EmailMessage(
                topic,
                text,
                'reporter@intel.com',
                to_emails,
                cc=['Arseniy.Obolenskiy@intel.com'],
            )
            msg.content_subtype = 'html'
            msg.send()
        xlsx = Path(job.path)
        if xlsx.is_file():
            xlsx.unlink()
        job.save()
