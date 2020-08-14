import dataclasses
import logging
import re
from pathlib import Path
from tempfile import NamedTemporaryFile


from datetime import datetime
from typing import Tuple
from django.db import transaction
from django.utils import timezone
from django.core.files.storage import default_storage
from django.conf import settings
from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel as date_from_excel
from openpyxl.utils.datetime import CALENDAR_WINDOWS_1900
from openpyxl.worksheet.worksheet import Worksheet
from types import SimpleNamespace

from api.models import *
from api.serializers import create_serializer
from api.collate.caches import QueryCache
from api.collate.caches import ObjectsCache
from api.collate.gta_field_parser import GTAFieldParser
from utils import api_logging

from reporting.settings import production

""" Business logic """

log = logging.getLogger(__name__)
queryset_cache = QueryCache()
new_objects_ids = ObjectsCache()

NAME_MAPPING = {
    'buildversion': 'driverName',
    'item name': 'itemName',
    'args': 'itemArgs',
    'component': 'componentName',
    'execution start time': 'execStart',
    'execution end time': 'execEnd',
    'environment': 'envName',
    'operating system': 'osVersion',
    'operating system family': 'osName',
    'platform': 'platformName',
    'result key': 'resultKey',
    'status': 'status',
    'test run': 'testRun',
    'test session': 'testSession',
    'url': 'resultURL',
    'reason': 'reason',
    'vertical': 'vertical',
    'mapped component': 'mappedComponent',
}

REVERSE_NAME_MAPPING = {value: key for key, value in NAME_MAPPING.items()}
excel_base_date = CALENDAR_WINDOWS_1900


class ImportDescriptor:
    def __init__(self, pk=None, name=None, date=None, notes=None, source_file=None, force_run=False):
        if str(pk).strip() == '':
            pk = None

        if str(date).strip() == '':
            date = None

        if date is None:
            date = timezone.make_aware(datetime.now())

        self.validation = None
        self.pk = pk
        self.name = name
        self.notes = notes
        self.date = date
        self.source_file = source_file
        self.force_run = force_run in [True, 'True', 'on', 'true']


def get_temp_name() -> Path:
    folder = Path(settings.MEDIA_ROOT) / 'xlsx'
    if not folder.exists():
        folder.mkdir(exist_ok=True, parents=True)

    fn = NamedTemporaryFile('w+', delete=False, dir=folder, suffix='.xlsx')
    fn.close()
    return Path(fn.name)


def import_results(file, descriptor, request):
    # check if file can be imported
    outcome, mapping = _verify_file(file, descriptor)

    if not outcome.is_success():
        log.debug('Interrupting import due to verification errors.')
        return outcome

    # store file content
    _store_results(file, request, mapping, descriptor)
    return outcome


def create_entities(entities):
    # 'entities' must be a list of dictionaries
    log.debug(f'Creating entities from raw data: {entities}')
    if type(entities) != list:
        raise EntityException("'entities' property must contain a list of objects.")

    for raw_entity in entities:
        # data sanity checks
        model_name = raw_entity.get('model', None)
        if model_name is None:
            raise EntityException(f"'model' property is missing in entity {raw_entity}")

        fields = raw_entity.get('fields', None)
        if fields is None:
            raise EntityException(f"'fields' property is missing in entity {raw_entity}")

        # deserialize data to entity object
        serializer = create_serializer(model_name, data=fields)
        if serializer is None:
            raise EntityException(f"Serializer for model '{model_name}' is not found.")

        if not serializer.is_valid():
            raise EntityException(f'Errors during {model_name} deserialization: {serializer.errors}')

        log.debug(f'Checking if entity exists: {serializer.validated_data}')

        existing_entity = serializer.Meta.model.objects.filter(**serializer.validated_data).first()
        if existing_entity is not None:
            raise EntityException(f'Attempting to create already existing entity with id {existing_entity.id}')

        # save entity
        log.debug(f'Saving entity {serializer.validated_data}')
        serializer.save()


def _get_column_values(column_name, rows, column_mapping):
    next(rows)
    return [row[column_mapping[column_name]].value for row in non_empty_row(rows)]


@transaction.atomic
def _store_results(xlsx, request, mapping: Tuple[Worksheet, dict], descriptor: ImportDescriptor):
    # Assuming that all related objects already exist.
    sheet, _ = mapping
    rows = sheet.rows
    next(rows)

    # Save transient validation entity
    if descriptor.validation.pk is None:
        descriptor.validation.save()

    tmp_name = get_temp_name()
    with default_storage.open(tmp_name, 'wb+') as destination:
        for chunk in xlsx.chunks():
            destination.write(chunk)

    requester = api_logging.get_user_object(request)
    obj = ImportJob.objects.create(path=tmp_name, requester=requester)
    obj.save()
    # Start background part of import
    if not request.data.get("disable_background_task", False):
        # "disable_background_task" flag is used ONLY for tests.
        # If this flag is used validation will not be saved!
        from .tasks import do_import
        do_import.send(obj.id, descriptor.validation.pk, descriptor.force_run)


def _namespace_to_dict(namespace):
    return dict(namespace.__dict__)

def _verify_file(file, descriptor):
    global excel_base_date

    outcome = OutcomeBuilder()

    # try to open file as excel workbook
    log.debug(f'Verifying file of type {type(file)}')
    try:
        workbook = load_workbook(file)
    except Exception as e:
        message = getattr(e, 'message', repr(e))
        log.warning(f'Failed to open workbook: {message}')
        outcome.add_workbook_error(message)
        return outcome, None

    log.debug('workbook is opened.')

    # read excel base date from workbook property
    excel_base_date = workbook.excel_base_date

    # decide which sheet will be used as data source
    mapping = _get_best_sheet_mapping(workbook)
    sheet, column_mapping = mapping
    if sheet is None:
        existing_columns = set(column_mapping.keys())
        missing_columns = ', '.join(
            key for key, value in NAME_MAPPING.items() if value not in existing_columns
        )
        outcome.add_missing_columns_error(missing_columns)

        log.debug('Verification failed due to sheet mapping errors.')
        return outcome, None

    log.debug(f"Using sheet '{sheet.title}'")

    # Purge all cached entities
    queryset_cache.clear()
    new_objects_ids.clear()

    # Create Validation entity
    if not _build_validation(descriptor, mapping, outcome):
        # Resume file content validation to collect all other possible warnings
        log.error("Unable to read or create Validation using file content.")

    validation = descriptor.validation

    # Verification and preparing lookup tables before insertion
    rows = sheet.rows
    next(rows)
    effective_max_row = 0

    # get list of result urls
    url_list = _get_column_values('resultURL', sheet.rows, column_mapping)

    # process file content row by row.
    for row in non_empty_row(rows):
        effective_max_row += 1

        # verify row content
        builder = RecordBuilder(validation, row, column_mapping, outcome, url_list=url_list)
        builder.verify(descriptor.force_run)

    log.debug('processed all rows.')

    # Verify that os, env and platform columns contain only one distinct value.
    for column_key in ['osName', 'osVersion', 'envName', 'platformName']:

        distinct_values = set(_get_column_values(column_key, sheet.rows, column_mapping))

        if len(distinct_values) > 1:
            column_name = REVERSE_NAME_MAPPING[column_key]
            message = f"Column '{column_name}' contains several distinct values."

            outcome.add_ambiguous_column_error(column_name, list(distinct_values))
            outcome.add_warning(message)

            log.error(message)

    return outcome, mapping


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



def _get_best_sheet_mapping(workbook):
    column_mapping = {}

    for title in [workbook.worksheets[0].title, 'best', 'all']:
        if title in workbook.sheetnames:
            sheet = workbook[title]
            column_mapping = _create_column_mapping(workbook[title])

            if len(column_mapping) >= 15:
                return sheet, column_mapping

    return None, column_mapping


def _create_column_mapping(sheet):
    captions = next(sheet.rows)
    column_mapping = dict()

    for cell in captions:
        if cell.value is None:
            continue

        mapped_name = NAME_MAPPING.get(str(cell.value).lower(), None)
        if mapped_name is not None:
            column_mapping[mapped_name] = cell.column - 1

    return column_mapping


def _build_validation(descriptor, mapping, outcome):
    # sanity check
    if descriptor.validation is not None:
        return False

    # Use existing validation if validation_id was provided
    if descriptor.pk is not None:
        validation = Validation.objects.filter(pk=descriptor.pk).first()

        if validation is None:
            outcome.add_invalid_validation_error(f'Validation with id {descriptor.pk} does not exist.')
            return False

        descriptor.validation = validation
        return True

    sheet, column_mapping = mapping
    rows = sheet.rows

    # use 2nd row of related worksheet as data source
    try:
        next(rows)
        row = next(rows)
        if set(cell.value for cell in row) == {None}:
            raise StopIteration()
    except StopIteration:
        message = f"Worksheet '{sheet.title}' is empty."
        log.error(message)

        outcome.add_workbook_error(message)
        return False

    # read fields for Validation creation from data source
    builder = RecordBuilder(None, row, column_mapping, outcome)
    if not builder.verify(force_run=True):
        log.debug('Unable to build Validation object based on 2nd row of the file.')
        return False

    fields = builder.get_fields()
    query_filter = dict(
        name=descriptor.name,
        env=fields.env,
        platform=fields.platform,
        os=fields.os,
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
        notes=descriptor.notes,
        date=descriptor.date,
        source_file=descriptor.source_file,
    )

    log.debug(f'Composed new transient validation')
    descriptor.validation = validation

    return True


# generator that stops row iteration on first empty row
def non_empty_row(rows):
    while True:
        try:
            row = next(rows)
        except StopIteration:
            break

        if set(cell.value for cell in row) == {None}:
            break

        yield row


class OutcomeBuilder:
    def __init__(self):
        self.success = False
        self.errors = list()
        self.warnings = dict()
        self.changes = dict(added=0, updated=0, skipped=0)

    def build(self):
        outcome = {}
        success = self.is_success()
        if success:
            outcome = dict(
                success=success,
                changes=self.changes,
            )
        else:
            outcome = dict(
                success=success,
                errors=self.errors,
                warnings=self.warnings,
            )

        return outcome

    def is_success(self):
        return len(self.errors) + len(self.warnings) == 0

    def add_warning(self, warning):
        self.warnings[warning] = self.warnings.get(warning, 0) + 1

    def __add_error(self, code, message, **kwargs):
        err = dict(code=code, message=message, **kwargs)
        if err not in self.errors:
            self.errors.append(err)

    def add_invalid_validation_error(self, message):
        self.__add_error('ERR_INVALID_VALIDATION_ID', message)

    def add_existing_validation_error(self, message, fields_data):
        fields = {str(key): str(value) for (key, value) in fields_data}
        entity = dict(model='Validation', fields=fields)

        self.__add_error('ERR_EXISTING_VALIDATION', message, entity=entity)

    def add_missing_field_error(self, missing_field, is_alias=False):
        model_name, fields = missing_field
        entity=dict(model=model_name, fields=fields)

        if is_alias:
            self.add_warning(f"{model_name} with name or alias '{fields['name']}' does not exist.")
        else:
            self.add_warning(f'{model_name} with properties {fields} does not exist.')

        self.__add_error('ERR_MISSING_ENTITY', f'Missing field {missing_field}', entity=entity)

    def add_missing_columns_error(self, columns):
        message = 'Not all columns found, please check import file for correctness.'
        self.__add_error('ERR_MISSING_COLUMNS', message, values=columns)

    def add_workbook_error(self, message):
        self.__add_error('ERR_WORKBOOK_EXCEPTION', message)

    def add_ambiguous_column_error(self, column, values):
        message = 'Two or more distinct values in column'
        self.__add_error('ERR_AMBIGUOUS_COLUMN', message, column=column, values=values)

    def add_existing_run_error(self, run):
        message = f"Run with name '{run.name}' and session '{run.session}' already exist."
        self.add_warning(message)
        self.__add_error('ERR_EXISTING_RUN', message)

    def add_date_format_error(self, date, field_type='string'):
        message=f'Unable to auto-convert {field_type} "{date}" to excel date.'
        self.__add_error('ERR_DATE_FORMAT', message)


class RecordBuilder:
    def __init__(self, validation, row, column_mapping, outcome, url_list=None):
        self.__row = row
        self.__columns = dict((key, row[index].value) for key, index in column_mapping.items())
        self.validation = validation
        self.__outcome = outcome
        self.__record = SimpleNamespace(
            validation=None,
            env=None,
            component=None,
            item=None,
            run=None,
            status=None,
            platform=None,
        )
        self.__url_list = url_list

    def verify(self, force_run=False):
        columns = self.__columns
        record = self.__record

        record.validation = self.validation
        record.env = self._find_object(Env, name=columns['envName'])
        record.component = self._find_object(Component, name=columns['componentName'])
        record.item = self._find_object(Item, name=columns['itemName'], args=columns['itemArgs'])
        record.status = self._find_object(Status, test_status=columns['status'])
        record.platform = self._find_with_alias(Platform, columns['platformName'])

        record.os = self._find_with_alias(Os, columns['osVersion'], ignore_warnings=True)
        if record.os is None:
            record.os = self._find_with_alias(Os, columns['osName'])

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

    def _get_or_create(self, cls, obj):
        kwargs = dataclasses.asdict(obj)
        try:
            return cls.objects.get(**kwargs)
        except cls.DoesNotExist:
            return cls(**kwargs)

    def build(self, force_run=False):
        if not self.verify(force_run):
            return None

        record = self.__record
        fields = _namespace_to_dict(self.__record)

        # Ensure that all fields are present.
        if not self.__check_fields_existance(fields):
            self.__notify_missing_fields(fields)
            return None

        record = self.__record
        fields = self.__record.__dict__
        # Retrieve additional fields from GTA API
        if self.__columns['resultURL'] not in GTAFieldParser.result.keys():
            log.debug(f'Missing job key {self.__columns["resultURL"]}, started retrieving...')
            GTAFieldParser(
                self.__columns['testRun'], self.__columns['testSession'],
                self.__columns['mappedComponent'], self.__columns['vertical'],
                self.__columns['platformName'], self.__url_list).process()
        if self.__columns['resultURL'] in GTAFieldParser.result.keys():
            res = GTAFieldParser.result[self.__columns['resultURL']]
            log.debug(f"{self.__columns['resultURL']}")
            record.driver = self._get_or_create(Driver, res['driver'])
            record.scenario_asset = self._get_or_create(ScenarioAsset, res['scenario'])
            record.msdk_asset = self._get_or_create(MsdkAsset, res['msdk'])
            record.os_asset = self._get_or_create(OsAsset, res['os_image'])
            record.lucas_asset = self._get_or_create(LucasAsset, res['lucas'])
            record.fulsim_asset = self._get_or_create(FulsimAsset, res['fulsim'])
            record.simics = self._get_or_create(Simics, res['simics'])
        else:
            log.error(f'Missing key {self.__columns["resultURL"]}')

        # Create entities automatically if they was not found in database during import.
        for obj, cls in (
            (record.run, Run),
            (record.driver, Driver),
            (record.scenario_asset, ScenarioAsset),
            (record.msdk_asset, MsdkAsset),
            (record.os_asset, OsAsset),
            (record.lucas_asset, LucasAsset),
            (record.fulsim_asset, FulsimAsset),
            (record.simics, Simics),
        ):
            if obj.id is None:
                obj.save()
                new_objects_ids.update(cls, obj.id)

        entity = Result()
        for key, value in fields.items():
            setattr(entity, key, value)

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

        entity.result_key = self.__columns['resultKey']
        entity.result_url = self.__columns['resultURL']
        entity.result_reason = self.__columns['reason']

        # Update existing result if new status priority is greater than or equal to existing.
        existing_entity = _find_existing_entity(entity)
        if existing_entity is not None:
            if entity.status.priority < existing_entity.status.priority:
                entity = None
            else:
                for attribute in ['run', 'status', 'result_key', 'result_url', 'exec_start', 'exec_end', 'driver']:
                    setattr(existing_entity, attribute, getattr(entity, attribute))
                entity = existing_entity

        # Assign item group if necessary
        if entity is not None:
            item = entity.item
            if item.group is None:
                group = _find_group(item.name)
                if group is not None:
                    item.group = group
                    item.save()

        return entity

    def get_fields(self):
        return SimpleNamespace(**self.__record.__dict__)

    def _find_object(self, cls, ignore_warnings=False, **params):
        for obj in queryset_cache.get(cls):
            if self.__match_by_params(obj, params):
                return obj

        self._notify_object_not_found(cls, params, ignore_warnings)
        return None

    def _find_with_alias(self, cls, alias, ignore_warnings=False):
        if alias is None:
            return None

        for obj in queryset_cache.get(cls):
            if self.__match_by_alias(obj, alias):
                return obj

        self._notify_alias_not_found(cls, alias, ignore_warnings)
        return None

    def __match_by_params(self, obj, params):
        found = True

        for key, value in params.items():
            # case insensitive strings compare
            if type(value) != str:
                found &= getattr(obj, key) == value
            else:
                attr = getattr(obj, key, None)

                if attr is not None:
                    found &= attr.lower() == value.lower()
                else:
                    found = False
                    break

        return found

    def __match_by_alias(self, obj, name):
        ignore_case_name = name.lower()

        if obj.name.lower() == ignore_case_name:
            return True

        if obj.aliases is None:
            return False

        if ignore_case_name in self.__iterate_aliases(obj.aliases):
            return True

        return False

    def __check_fields_existance(self, fields):
        return None not in fields.values()

    def __notify_missing_fields(self, fields):
        missing_fields = [x[0] for x in fields.items() if x[1] is None]
        message = f'Corrupted validation of column "{self.__row[0].row}": missing fields {missing_fields}'

        log.debug(message)
        self.__outcome.add_workbook_error(message)

    def _notify_object_not_found(self, cls, params, ignore_warnings):
        if not ignore_warnings:
            self.__outcome.add_missing_field_error((cls.__name__, params))

    def _notify_alias_not_found(self, cls, name, ignore_warnings):
        if not ignore_warnings:
            self.__outcome.add_missing_field_error((cls.__name__, dict(name=name)), is_alias=True)

    def __iterate_aliases(self, aliases):
        return (x for x in map(str.strip, aliases.lower().split(';')) if x)


class EntityException(Exception):
    pass
