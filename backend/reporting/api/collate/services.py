import dataclasses
import logging
import re

from pathlib import Path
from tempfile import NamedTemporaryFile
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from openpyxl.utils.datetime import from_excel as date_from_excel
from openpyxl.utils.datetime import CALENDAR_WINDOWS_1900

from api.models import Component, Env, Item, Os, Run, Platform, Result, ResultGroupMask, ResultGroupNew, Validation, \
    Status

from api.collate.gta_field_parser import GTAFieldParser
from api.collate.excel_utils import REVERSE_NAME_MAPPING
from api.collate.excel_utils import open_excel_file
from api.collate.excel_utils import non_empty_row
from api.collate.business_entities import ResultData
from api.utils.caches import QueryCache, ObjectsCache, queryset_cache
from api.utils.cached_objects_find import find_object, find_with_alias, find_testitem_object

""" Business logic """

log = logging.getLogger(__name__)
new_objects_ids = ObjectsCache()
parser = GTAFieldParser()

excel_base_date = CALENDAR_WINDOWS_1900


def get_temp_name() -> Path:
    folder = Path(settings.MEDIA_ROOT) / 'xlsx'
    if not folder.exists():
        folder.mkdir(exist_ok=True, parents=True)

    fn = NamedTemporaryFile('w+', delete=False, dir=folder, suffix='.xlsx')
    fn.close()
    return Path(fn.name)


def verify_file(context):
    global excel_base_date

    outcome = context.outcome

    # try to open file as excel workbook
    log.debug(f'Verifying file of type {type(context.request.file)}')

    workbook = open_excel_file(context.request.file, outcome)
    if workbook is None:
        return

    log.debug('workbook is opened.')

    # read excel base date from workbook property
    excel_base_date = workbook.excel_base_date

    # decide which sheet will be used as data source
    if not context.mapping.set_from_workbook(workbook, outcome):
        log.debug('Verification failed due to sheet mapping errors.')
        return

    sheet = context.mapping.sheet
    log.debug(f"Using sheet '{sheet.title}'")

    # Purge all cached entities
    queryset_cache.clear()
    new_objects_ids.clear()

    # Create Validation entity
    if not _build_validation(context):
        # Resume file content validation to collect all other possible warnings
        log.error("Unable to read or create Validation using file content.")

    # Verification and preparing lookup tables before insertion
    rows = sheet.rows
    next(rows)
    effective_max_row = 0

    # process file content row by row.
    for row in non_empty_row(rows):
        effective_max_row += 1

        # verify row content
        builder = RecordBuilder(context, row)
        builder.verify(context.request.force_run)

    log.debug('processed all rows.')

    # Verify that os, env and platform columns contain only one distinct value.
    for column_key in ['osName', 'osVersion', 'envName', 'platformName']:

        distinct_values = set(context.mapping.get_column_values(column_key))

        if len(distinct_values) > 1:
            column_name = REVERSE_NAME_MAPPING[column_key]
            message = f"Column '{column_name}' contains several distinct values."

            outcome.add_ambiguous_column_error(column_name, list(distinct_values))
            outcome.add_warning(message)

            log.error(message)


def _find_existing_entity(reference):
    try:
        return Result.objects.get(
            validation_id=reference.validation.id,
            platform_id=reference.platform.id,
            item_id=reference.item.id,
            env_id=reference.env.id,
            os_id=reference.os.id
        )
    except (Result.DoesNotExist, Result.MultipleObjectsReturned):
        return None


def _find_group(item_name):
    group_mask_queryset = queryset_cache.get(ResultGroupMask)

    for group_mask in group_mask_queryset:
        if re.match(group_mask.mask, item_name):
            return group_mask.group

    try:
        return ResultGroupNew.objects.get(name='Unknown')
    except (ResultGroupNew.DoesNotExist, ResultGroupNew.MultipleObjectsReturned):
        return None


def _build_validation(context):
    # sanity check
    if context.validation is not None:
        return False

    outcome = context.outcome
    validation_id = context.request.validation_id

    # Use existing validation if validation_id was provided
    if validation_id is not None:
        validation = Validation.objects.filter(pk=validation_id).first()

        if validation is None:
            outcome.add_invalid_validation_error(f'Validation with id {validation_id} does not exist.')
            return False

        context.validation = validation
        return True

    rows = context.mapping.sheet.rows

    # use 2nd row of related worksheet as data source
    try:
        next(rows)
        row = next(rows)
        if set(cell.value for cell in row) == {None}:
            raise StopIteration()
    except StopIteration:
        message = f"Worksheet '{context.mapping.sheet.title}' is empty."
        log.error(message)

        outcome.add_workbook_error(message)
        return False

    # read fields for Validation creation from data source
    builder = RecordBuilder(context, row)
    if not builder.verify(force_run=True):
        log.debug('Unable to build Validation object based on 2nd row of the file.')
        return False

    request = context.request
    fields = builder.get_fields()
    query_filter = dict(
        name=request.name,
        env=fields['env'],
        platform=fields['platform'],
        os=fields['os'],
    )

    # Validation record must have unique group of fields
    if Validation.objects.filter(**query_filter).exists():
        parameters = ", ".join(f"{key}: '{value}'" for (key, value) in query_filter.items())
        message = 'Validation with such parameters already exists'
        outcome.add_existing_validation_error(message, query_filter.items())
        log.error(f'{message} {parameters}.')
        return False

    validation = Validation(
        **query_filter,
        notes=request.notes,
        date=request.date,
        source_file=request.source_file,
        owner=request.requester,
    )

    log.debug(f'Composed new transient validation')
    context.validation = validation

    return True


class RecordBuilder:
    def __init__(self, context, row):
        self.__mapping = context.mapping
        self.__row = row
        self.__columns = dict((key, row[index].value)
                for key, index in self.__mapping.column_mapping.items())
        self.validation = context.validation
        self.__outcome = context.outcome
        self.__data = ResultData()

    def verify(self, force_run=False):
        columns = self.__columns
        record = self.__data.mandatory

        record.validation = self.validation
        record.env = self._find_object(Env, name=columns['envName'])
        record.component = self._find_object(Component, name=columns['componentName'])
        record.item = self._find_testitem_object(name=columns['itemName'], args=columns['itemArgs'])
        record.status = self._find_object(Status, test_status=columns['status'])
        record.platform = self._find_with_alias(Platform, columns['platformName'])

        record.os = self._find_with_alias(Os, columns['osVersion'])

        # Create Run entities automatically if they was not found in database during import. If found - send warning.
        try:
            record.run = Run.objects.get(name=columns['testRun'], session=columns['testSession'])
            if not force_run and not new_objects_ids.is_known(Run, record.run.id):
                self.__outcome.add_existing_run_error(record.run)
        except (Run.DoesNotExist, Run.MultipleObjectsReturned):
            record.run = Run(name=columns['testRun'], session=columns['testSession'])

        # Check if date can be parsed
        for field_name in ['execStart', 'execEnd']:
            date = columns[field_name]
            # check if value is excel's date using floating point representation
            if type(date) == str:
                try:
                    float(date)
                except ValueError:
                    self.__outcome.add_date_format_error(date)

            elif type(date) not in [datetime, float, type(None)]:
                self.__outcome.add_date_format_error(date, type(date))

        return self.__outcome.is_success()

    def build(self, force_run=False):
        if not self.verify(force_run):
            return None

        # Ensure that all mandatory fields are present.
        if not self.__data.mandatory.is_valid():
            self.__notify_missing_fields()
            return None

        self.__retrieve_extra_fields()
        self.__data.save_transient()

        entity = Result()
        self.__set_model_fields(entity)
        self.__set_model_datetime_range(entity)

        entity = self.__update_if_exists(entity)
        self.__assign_and_save_group(entity)

        return entity

    def __retrieve_extra_fields(self):
        # Retrieve additional fields from GTA API
        result_url = self.__columns['resultURL']
        if not parser.is_cached(result_url):
            log.debug(f'Missing job key {result_url}, started retrieving...')

            constraint = self.__create_parser_constraint()
            url_list = self.__mapping.get_column_values('resultURL')

            parser.fetch_from(*constraint, url_list)

        if parser.is_cached(result_url):
            log.debug(f"using GTAFieldParser cached values: {result_url}")
            self.__data.extra = parser.create_result_data(result_url)

        else:
            log.error(f'Missing key {result_url}')

    def __create_parser_constraint(self):
        return tuple(self.__columns[x] for x in [
            'testRun',
            'testSession',
            'mappedComponent',
            'vertical',
            'platformName',
        ])

    def __set_model_fields(self, entity):
        for key, value in self.get_fields().items():
            setattr(entity, key, value)

        entity.result_key = self.__columns['resultKey']
        entity.result_url = self.__columns['resultURL']
        entity.result_reason = self.__columns['reason']

    def __set_model_datetime_range(self, entity):
        # Set exec_start and exec_end model attributes
        for attribute, field in [('exec_start', 'execStart'), ('exec_end', 'execEnd')]:
            date = self.__columns[field]
            if date is None:
                date = timezone.now().replace(microsecond=0)
            elif type(date) == float:
                date = timezone.make_aware(date_from_excel(date, excel_base_date))
                log.debug(f"used excel_base_date: {excel_base_date}")
            elif type(date) == str:
                date = timezone.make_aware(date_from_excel(float(date), excel_base_date))
                log.debug(f"used excel_base_date from string: {excel_base_date}")
            elif timezone.is_naive(date):
                date = timezone.make_aware(date)

            setattr(entity, attribute, date)

    def __update_if_exists(self, entity) -> Result :
        # Update existing result if new status priority is greater than or equal to existing.
        existing_entity = _find_existing_entity(entity)

        if existing_entity is not None:
            if entity.status.priority < existing_entity.status.priority:
                entity = None
            else:
                for attribute in ['run', 'status', 'result_key', 'result_url', 'exec_start', 'exec_end', 'driver']:
                    setattr(existing_entity, attribute, getattr(entity, attribute))
                entity = existing_entity

        return entity

    def __assign_and_save_group(self, entity):
        if entity is not None:
            item = entity.item
            if item.group is None:
                group = _find_group(item.name)
                if group is not None:
                    item.group = group
                    item.save()

    def get_fields(self):
        return self.__data.get_fields()

    def _find_object(self, cls, ignore_warnings=False, **params):
        obj = find_object(cls, **params)
        if obj is not None:
            return obj

        self._notify_object_not_found(cls, params, ignore_warnings)
        return None

    def _find_testitem_object(self, ignore_warnings=False, **params):
        obj = find_testitem_object(**params)
        if obj is not None:
            return obj

        self._notify_object_not_found(Item, {'name': params['name'], 'args': params['args']}, ignore_warnings)
        return None

    def _find_with_alias(self, cls, alias, ignore_warnings=False):
        if alias is None:
            return None

        obj = find_with_alias(cls, alias)
        if obj is not None:
            return obj

        self._notify_alias_not_found(cls, alias, ignore_warnings)
        return None

    def __check_fields_existance(self, fields):
        return None not in fields.values()

    def __notify_missing_fields(self):
        fields = dataclasses.asdict(self.__data.mandatory)
        missing_fields = [key for key, value in fields.items() if value is None]
        message = f'Corrupted validation of row "{self.__row[0].row}": missing fields {missing_fields}'

        log.debug(message)
        self.__outcome.add_workbook_error(message)

    def _notify_object_not_found(self, cls, params, ignore_warnings):
        if not ignore_warnings:
            self.__outcome.add_missing_field_error((cls.__name__, params))

    def _notify_alias_not_found(self, cls, name, ignore_warnings):
        if not ignore_warnings:
            self.__outcome.add_missing_field_error((cls.__name__, dict(name=name)), is_alias=True)
