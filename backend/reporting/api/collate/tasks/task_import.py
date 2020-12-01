import dataclasses
import logging

from pathlib import Path
from typing import Dict, Union, Optional, List
from dramatiq import actor

from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.db import transaction
from django.template.loader import get_template

from api.models import ImportJob, Result, ResultFeature
from api.models import JobStatus
from api.collate.business_entities import Context
from api.collate.business_entities import ValidationDTO
from api.collate.excel_utils import open_excel_file
from api.collate.excel_utils import non_empty_row
from api.collate.services import RecordBuilder
from api.collate.services import replace_unknown_os
from reporting.settings import production, AUTH_USER_MODEL

log = logging.getLogger(__name__)


@dataclasses.dataclass
class Changes:
    added: int = 0
    updated: int = 0
    skipped: int = 0

    def update_from_entity(
        self,
        entity: Optional[Result],
        requester: AUTH_USER_MODEL,
        reason: str,
        features: Optional[List[ResultFeature]]) -> None:

        if entity is None:
            self.skipped += 1
        elif entity.id is None:
            entity.save(skip_stats_update=True)
            self.added += 1
        elif entity.get_changed_columns():
            entity._change_reason = reason
            entity._history_user = requester
            entity._changed = True
            entity.save(skip_stats_update=True)
            entity.features.set(features)
            self.updated += 1
        else:
            self.skipped += 1


@actor(time_limit=86400000)  # tasks can execute for up to a day
@transaction.atomic
def do_import(job_id: int, validation_dict: Dict[str, Optional[Union[str, int]]], reason: str) -> None:
    topic = 'Reporter: <unknown>'
    text = ''
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
        replace_unknown_os(context)
        changes = Changes()
        rows = context.mapping.sheet.rows
        next(rows)

        # Process file content row by row and perform queries to get additional data
        for row in non_empty_row(rows):
            builder = RecordBuilder(context, row)
            entity, features = builder.build(job.force_run, job.force_item)
            changes.update_from_entity(entity, job.requester, reason, features)

        outcome.changes = dataclasses.asdict(changes)

        log.debug('File store outcome: %s', outcome.build())

        vstats = validation.update_status_counters()
        c_and_f = validation.update_components_and_features()
        validation.save()

        log.info('Imported validation details:')
        log.info('  Item statuses: %s', vstats.__format__('full'))
        log.info('  Components: %s', c_and_f.components_as_str())
        log.info('  Features: %s', c_and_f.features_as_str())

        log.debug('Removing temporary xlsx: %s', job.path)
        xlsx = Path(job.path)
        if xlsx.is_file():
            xlsx.unlink()
    except Exception:
        log.exception("Import job failed")
        # Get list of staff e-mails to report an error
        to_emails += get_user_model().staff_emails()
        text = f'Import of validation <b>{validation_info}</b> failed.'
        topic = f'Reporter: import of validation {validation_info} failed'
        job.status = JobStatus.FAILED
    else:
        template = get_template('collate/import_message.html')
        ctx = {'validation_info': validation_info,
               'added': changes.added,
               'updated': changes.updated,
               'skipped': changes.skipped,
               'site_url': job.site_url,
               'validation_id': context.get_validation_id()}
        text = template.render(ctx)
        topic = f'Reporter: import of validation {validation_info} completed'
        job.status = JobStatus.DONE
    finally:
        log.info("Sending an e-mail...")
        log.info("To: %s", ", ".join(to_emails))
        log.info("Subject: %s", topic)

        if production:
            # None in the from field means that emails will be send from
            # DEFAULT_FROM_EMAIL setting address
            msg = EmailMessage(
                topic,
                text,
                None,
                to_emails,
            )
            msg.content_subtype = 'html'
            msg.send()

        job.save()
