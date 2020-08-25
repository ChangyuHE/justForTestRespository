import dataclasses
import logging
from pathlib import Path

import dramatiq
from django.template import Template, Context

from ..models import ImportJob
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from api.collate import services
from api.models import Validation
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
def do_import(job_id: int, validation_id: int, force_run: bool, site_url: str):
    to_emails = []
    validation_info = '<unknown>'

    try:
        job = ImportJob.objects.get(pk=job_id)
        log.debug("Started task: username=%s, table path: %s", job.requester.username, job.path)
        if job.requester.email:
            to_emails.append(job.requester.email)

        validation = Validation.objects.get(pk=validation_id)
        validation_info = validation.name
        # Load workbook
        try:
            workbook = services.load_workbook(job.path)
        except Exception as e:
            message = getattr(e, 'message', repr(e))
            log.warning('Failed to open workbook: %s', message)
            return
        # Get necessary data from workbook
        mapping = services._get_best_sheet_mapping(workbook)
        sheet, column_mapping = mapping
        url_list = services._get_column_values('resultURL', sheet.rows, column_mapping)

        outcome = services.OutcomeBuilder()
        changes = Changes()
        rows = sheet.rows
        next(rows)
        # Process file content row by row and perform queries to get additional data
        for row in services.non_empty_row(rows):
            builder = services.RecordBuilder(validation, row, column_mapping, outcome, url_list=url_list)
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
        context = Context({'validation_info': validation_info,
                           'added': changes.added,
                           'updated': changes.updated,
                           'skipped': changes.skipped,
                           'site_url': site_url,
                           'validation_id': validation_id})
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
