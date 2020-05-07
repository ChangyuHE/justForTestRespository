import logging
import re

from datetime import datetime
from django.utils import timezone
from openpyxl import load_workbook
from types import SimpleNamespace

from api.models import Env
from api.models import Driver
from api.models import Component
from api.models import Item
from api.models import Os
from api.models import Run
from api.models import Status
from api.models import Platform
from api.models import Validation
from api.models import Result
from api.models import ResultGroupMask

from api.serializers import createSerializer

""" Business logic """

log = logging.getLogger(__name__)
queryset_cache = dict()
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
}


def import_results(file, validation_id):
    # validation_id must refer to existing Validation
    validation = _get_validation(validation_id)

    if validation is None:
        outcome = OutcomeBuilder()
        outcome.add_invalid_validation_error(validation_id)

        return outcome

    # check if file can be imported
    outcome, mapping = _verify_file(file, validation)

    if not outcome.success:
        return outcome

    # store file content
    outcome = _store_results(mapping, validation)
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
        serializer = createSerializer(model_name, data=fields)
        if serializer is None:
            raise EntityException(f"Serializer for model '{model_name}' is not found.")

        if not serializer.is_valid():
            raise EntityException(f'Errors during {model_name} deserialization: {serializer.errors}')

        log.debug(f'Checking if entity exists: {serializer.validated_data}')

        # check if entity already exists in db
        ignore_case_data = dict()
        for key, value in serializer.validated_data.items():
            if type(value) == str:
                key += '__iexact'
            ignore_case_data[key] = value

        existing_entity = serializer.Meta.model.objects.filter(**ignore_case_data).first()
        if existing_entity is not None:
            log.warning(f'Attempting to create already existing entity with id {existing_entity.id}')
            continue

        # save entity
        log.debug(f'Saving entity {serializer.validated_data}')
        serializer.save()


def _get_validation(validation_id):
    # retrieve Validation object from db
    try:
        return Validation.objects.get(pk=validation_id)
    except Validation.DoesNotExist:
        pass

    log.error(f"Validation with id '{validation_id}' does not exist.")
    return None


def _store_results(mapping, validation):
    # Assuming that all related objects already exist.
    sheet, column_mapping = mapping
    rows = sheet.rows
    next(rows)
    changes = SimpleNamespace(added=0, updated=0, skipped=0)

    # process file content row by row.
    # TODO: bulk save to db
    for row in rows:
        builder = RecordBuilder(validation, row, column_mapping)
        entity = builder.build()

        if entity is None:
            changes.skipped += 1
        elif entity.id is None:
            entity.save()
            changes.added += 1
        else:
            entity.save()
            changes.updated += 1

    outcome = OutcomeBuilder()
    outcome.success = True
    outcome.changes = changes.__dict__

    log.debug(f'File store outcome: {outcome.build()}')

    return outcome


def _verify_file(file, validation):
    # try to open file as excel workbook
    log.debug(f'Begin _verify_file, type: {type(file)}')
    try:
        workbook = load_workbook(file)
    except Exception as e:
        message = getattr(e, 'message', repr(e))
        log.warning(f'Failed to open workbook: {message}')
        outcome = OutcomeBuilder()
        outcome.add_workbook_error(message)
        return outcome, None

    log.debug('workbook is opened.')

    # decide which sheet will be used as data source
    sheet, column_mapping = _get_best_sheet(workbook)
    if sheet is None:
        reverse_name_mapping = {value: key for key, value in NAME_MAPPING.items()}
        missing_columns = ', '.join(reverse_name_mapping[key] for key in column_mapping.keys())
        outcome = OutcomeBuilder()
        outcome.add_missing_columns_error(missing_columns)

        return outcome, None

    log.debug(f"Using sheet '{sheet.title}'")

    # Verification and preparing lookup tables before insertion
    queryset_cache.clear()
    is_valid = True
    rows = sheet.rows
    outcome = OutcomeBuilder()
    next(rows)

    for row in rows:
        # verify row content
        builder = RecordBuilder(validation, row, column_mapping)
        is_valid &= builder.verify()

        # gather warnings after verification
        for warning in builder.get_warnings():
            outcome.add_warning(warning)

        # gather missing entities info
        for missing_field in builder.get_suggested_fields().items():
            outcome.add_missing_field_error(missing_field)

    log.debug('processed all rows.')

    outcome.success = is_valid
    return outcome, (sheet, column_mapping)


def _find_existing_entity(reference):
    query = _get_cached_query(Result)

    for obj in query:
        if obj.validation_id == reference.validation.id \
                and obj.item_id == reference.item.id \
                and obj.platform_id == reference.platform.id \
                and obj.env_id == reference.env.id \
                and obj.os_id == reference.os.id:
            return obj
    return None


def _find_group(item_name):
    group_mask_queryset = _get_cached_query(ResultGroupMask)

    for group_mask in group_mask_queryset:
        if re.match(group_mask.mask, item_name):
            return group_mask.group

    return None


def _get_cached_query(cls):
    queryset_key = cls.__name__
    cached_query = queryset_cache.get(queryset_key, None)

    if cached_query is None:
        cached_query = cls.objects.all()
        queryset_cache[queryset_key] = cached_query

    return cached_query

def _clear_cache(classes=None):
    if classes is None:
        pass
    else:
        for cls in classes:
            queryset_cache.pop(cls.__name__, None)

def _get_best_sheet(workbook):
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

        mapped_name = NAME_MAPPING.get(cell.value.lower(), None)
        if mapped_name is not None:
            column_mapping[mapped_name] = cell.column

    return column_mapping


class OutcomeBuilder():
    def __init__(self):
        self.success = False
        self.errors = list()
        self.warnings = dict()
        self.changes = dict(added=0, updated=0, skipped=0)

    def build(self):
        outcome={}
        if self.success:
            outcome = dict(
                success=self.success,
                changes=self.changes,
            )
        else:
            outcome = dict(
                success=self.success,
                errors=self.errors,
                warnings=self.warnings,
            )

        return outcome

    def add_warning(self, warning):
        self.warnings[warning] = self.warnings.get(warning, 0) + 1

    def add_invalid_validation_error(self, validation_id):
        err = dict(
            code='ERR_INVALID_VALIDATION_ID',
            message=f'Validation with id {validation_id} does not exist.'
        )

        if err not in self.errors:
            self.errors.append(err)

    def add_missing_field_error(self, missing_field):
        model_name, fields = missing_field

        err = dict(
            code='ERR_MISSING_ENTITY',
            message=f'Missing field {missing_field}',
            entity=dict(model=model_name, fields=fields),
        )

        if err not in self.errors:
            self.errors.append(err)

    def add_missing_columns_error(self, columns):
        log.debug(f"missing column(s): {columns}")
        err = dict(
            code='ERR_MISSING_COLUMNS',
            message='Not all columns found, please check import file for correctness.' \
                + f' Missing columns: {columns}'
        )

        if err not in self.errors:
            self.errors.append(err)

    def add_workbook_error(self, message):
        log.debug(message)
        err = dict(
            code='ERR_WORKBOOK_EXCEPTION',
            message=message,
        )

        if err not in self.errors:
            self.errors.append(err)


class RecordBuilder():
    def __init__(self, validation, row, column_mapping):
        self.__row = row
        self.__warnings = list()
        self.__suggestions = dict()
        self.__columns = dict((key, row[index - 1].value) for key,index in column_mapping.items())
        self.validation = validation
        self.__record = SimpleNamespace(
            validation=None,
            env=None,
            driver=None,
            component=None,
            item=None,
            run=None,
            status=None,
            platform=None,
        )

    def verify(self):
        columns = self.__columns
        record = self.__record

        record.validation = self.validation
        record.env = self._find_object(Env, name=columns['envName'])
        record.driver = self._find_object(Driver, name=columns['driverName'])
        record.component = self._find_object(Component, name=columns['componentName'])
        record.item = self._find_object(Item, name=columns['itemName'], args=columns['itemArgs'])
        record.run = self._find_object(Run, name=columns['testRun'], session=columns['testSession'])
        record.status = self._find_object(Status, test_status=columns['status'])
        record.platform = self._find_with_alias(Platform, columns['platformName'])

        record.os = self._find_with_alias(Os, columns['osVersion'], ignore_warnings=True)
        if record.os is None:
            record.os = self._find_with_alias(Os, columns['osName'])

        # Check if date can be parsed
        for field_name in ['execStart', 'execEnd']:
            date = columns[field_name]
            if type(date) not in [datetime, None]:
                self.__warnings.append(f'Unable to auto-convert "{date}" to datetime.')

        is_valid = len(self.__warnings) <= 0
        return is_valid

    def build(self):
        if not self.verify():
            return None

        # Ensure that all fields are present.
        fields = self.__record.__dict__
        if None in fields.values():
            missing_fields = [x[0] for x in fields.items() if x[1] is None]
            message = f'Corrupted validation of column "{self.__row[0].row}": missing fields {missing_fields}'
            log.debug(message)
            self.__warnings.append(message)
            return None

        entity = Result()
        for key, value in fields.items():
            setattr(entity, key, value)

        # Set exec_start and exec_end model attributes
        for attribute, field in [('exec_start', 'execStart'), ('exec_end', 'execEnd')]:
            date = self.__columns[field]
            if date is None:
                date = timezone.now().replace(microsecond=0)
            elif timezone.is_naive(date):
                date = timezone.make_aware(date)

            setattr(entity, attribute, date)

        entity.result_key = self.__columns['resultKey']
        entity.result_url = self.__columns['resultURL']

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
        item = entity.item
        if item.group is None:
            group = _find_group(item.name)
            if group is not None:
                item.group = group
                item.save()

        return entity

    def get_warnings(self):
        return list(self.__warnings)

    def get_suggested_fields(self):
        return dict(self.__suggestions)

    def _find_object(self, cls, **params):
        cached_query = _get_cached_query(cls)

        for obj in cached_query:
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

            if found:
                return obj

        self.__warnings.append(f'{cls.__name__} with properties {params} does not exist.')
        self.__suggestions[cls.__name__] = params
        return None

    def _find_with_alias(self, cls, name, ignore_warnings=False):
        cached_query = _get_cached_query(cls)
        iname = name.lower()

        for obj in cached_query:
            if obj.name.lower() == iname \
                    or obj.aliases is not None \
                            and obj.aliases.lower().find(iname) >= 0:
                return obj

        if not ignore_warnings:
            self.__warnings.append(f"{cls.__name__} with name or aliases '{name}' does not exist.")
            self.__suggestions[cls.__name__] = dict(name=name)

        return None


class EntityException(Exception):
    pass
