import logging
import re

from datetime import datetime
from django.utils import timezone
from io import BytesIO
from openpyxl import load_workbook
from sys import exc_info
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

""" Business logic """
log = logging.getLogger(__name__)
queryset_cache = dict()

def import_results(file, validation_id):
    result, mapping = verify_results(file, validation_id)
    if not result.get('is_valid', False):
        return result

    result = store_results(mapping, validation_id)
    return result

def verify_results(file, validation_id):
    log.debug('Calling verify_file')
    result, mapping = verify_file(file)

    if not verify_validation(validation_id):
        result['is_valid'] = False
        warnings = result.get('warnings', None)

        if warnings is None:
            warnings = dict()
            result['warnings'] = warnings

        message = f'Validation with id {validation_id} does not exist.'
        warnings[message] = 1
        log.debug(message)

    return result, mapping

def store_results(mapping, validation_id):
    # Assuming that all related objects already exist.
    sheet, column_mapping = mapping
    rows = sheet.rows
    next(rows)
    validation = Validation.objects.get(pk=validation_id)
    changes = SimpleNamespace(added=0, updated=0, skipped=0)

    for row in rows:
        _, entity = __create_entity(validation, row, column_mapping)
        if entity is None:
            changes.skipped += 1
        elif entity.id is None:
            entity.save()
            changes.added += 1
        else:
            entity.save()
            changes.updated += 1

    return dict(is_valid=True, changes=changes.__dict__)

def verify_file(file):
    log.debug(f'Begin verify_file, type: {type(file)}')
    stream = BytesIO(file.read())
    try:
        workbook = load_workbook(stream)
    except:
        _, exc_value, *_ = exc_info()
        log.warning(f"Failed to open workbook: {exc_value}")
        return dict(is_valid=False, message=f'Verification failed: {exc_value}'), None
    finally:
        stream.close()

    log.debug('workbook is opened.')

    sheet, column_mapping = __get_best_sheet(workbook)
    if sheet is None:
        missing_columns = ', '.join(column_mapping.keys())
        log.debug(f'Missing columns {missing_columns}.')

        return dict(is_valid=False, message='Not all columns found, please check import file for correctness.' \
                + f' \nFound columns: {missing_columns}'), None

    # Verification and preparing lookup tables before insertion
    log.debug('best sheet is located.')
    queryset_cache.clear()
    sheet_warnings = {}
    rows = sheet.rows
    next(rows)

    for row in rows:
        row_warnings, _ = __create_entity(None, row, column_mapping, only_verify=True)
        for warning in row_warnings:
            sheet_warnings[warning] = sheet_warnings.get(warning, 0) + 1

    log.debug('processed all rows.')

    is_valid = len(sheet_warnings) <= 0
    message = f'File name: "{file.name}", size: {file.size}'
    message += f', rows: {sheet.max_row}, columns: {sheet.max_column}'

    log.debug('Finish verify_file.')
    return dict(is_valid=is_valid, message=message, warnings=sheet_warnings), (sheet, column_mapping)

def verify_validation(validation_id):
    log.debug(f'Checking if validation with id {validation_id} exists.')
    return Validation.objects.filter(pk=validation_id).exists()

def __create_entity(validation, row, column_mapping, only_verify=False):
    warnings = []
    get = lambda x: row[column_mapping[x] - 1].value
    record = SimpleNamespace()

    record.validation = validation
    record.env = __find_object(Env, warnings, name=get('envName'))
    record.driver = __find_object(Driver, warnings, name=get('driverName'))
    record.component = __find_object(Component, warnings, name=get('componentName'))
    record.item = __find_object(Item, warnings, name=get('itemName'), args=get('itemArgs'))
    record.run = __find_object(Run, warnings, name=get('testRun'), session=get('testSession'))
    record.status = __find_object(Status, warnings, test_status=get('status'))
    record.platform = __find_with_alias(Platform, warnings, get('platformName'))

    os_warnings = []
    record.os = __find_with_alias(Os, [], get('osVersion'))

    if record.os is None:
        record.os = __find_with_alias(Os, os_warnings, get('osName'))
    if record.os is None:
        warnings.extend(os_warnings)

    # Check if date can be parsed
    for field_name in ['execStart', 'execEnd']:
        date = get(field_name)
        if type(date) not in [datetime, None]:
            warnings.append(f'Unable to auto-convert "{date}" to datetime.')

    if only_verify:
        return warnings, None

    # Ensure that all fields are present.
    if None in record.__dict__.values():
        missing_fields = [x[0] for x in record.__dict__.items() if x[1] is None]
        message = f'Corrupted validation of column "{row[0].row}": missing fields {missing_fields}'
        log.debug(message)
        warnings.append(message)
        return warnings, None

    entity = Result()
    for key, value in record.__dict__.items():
        setattr(entity, key, value)

    # Set exec_start and exec_end model attributes
    for attribute, field in [('exec_start', 'execStart'), ('exec_end', 'execEnd')]:
        date = get(field)
        if date is None:
            date = timezone.now().replace(microsecond=0)
        elif timezone.is_naive(date):
            date = timezone.make_aware(date)

        setattr(entity, attribute, date)

    entity.result_key = get('resultKey')
    entity.result_url = get('resultURL')

    # Update existing result if new status priority is greater than or equal to existing.
    existing_entity = __find_existing_entity(entity)
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
        group = __find_group(item.name)
        if group is not None:
            item.group = group
            item.save()

    return warnings, entity

def __find_existing_entity(reference):
    query = __get_cached_query(Result)
    found = False

    for obj in query:
        if obj.validation_id == reference.validation.id \
                and obj.item_id == reference.item.id \
                and obj.platform_id == reference.platform.id \
                and obj.env_id == reference.env.id \
                and obj.os_id == reference.os.id :
            found = True
            break

    return obj if found else None

def __find_object(cls, warnings, **params):
    cached_query = __get_cached_query(cls)

    for obj in cached_query:
        found = True

        for key, value in params.items():

            if type(value) == str:
                found &= getattr(obj, key).lower() == value.lower()
            else:
                found &= getattr(obj, key) == value

        if found:
            return obj
    else:
        warnings.append(f"{cls.__name__} with properties {params} does not exist.")

    return None

def __find_with_alias(cls, warnings, name):
    cached_query = __get_cached_query(cls)
    iname = name.lower()
    found_obj = None

    for obj in cached_query:
        if obj.name.lower() == iname \
                or obj.aliases is not None \
                        and obj.aliases.lower().find(iname) >= 0:
            found_obj = obj

    if found_obj is None:
        warnings.append(f"{cls.__name__} with name or aliases '{name}' does not exist.")

    return found_obj

def __find_group(item_name):
    group_mask_queryset = __get_cached_query(ResultGroupMask)

    for group_mask in group_mask_queryset:
        if re.match(group_mask.mask, item_name):
            return group_mask.group

    return None

def __get_cached_query(cls):
    queryset_key = cls.__name__
    cached_query = queryset_cache.get(queryset_key, None)

    if cached_query is None:
        cached_query = cls.objects.all()
        queryset_cache[queryset_key] = cached_query

    return cached_query

def __get_best_sheet(workbook):
    column_mapping = {}

    for title in [workbook.worksheets[0].title, 'best', 'all']:
        if title in workbook.sheetnames:
            sheet = workbook[title]
            column_mapping = __create_column_mapping(workbook[title])

            if len(column_mapping) >= 15:
                return (sheet, column_mapping)

    return (None, column_mapping)

def __create_column_mapping(sheet):
    captions = next(sheet.rows)
    name_mapping = {
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
    column_mapping = dict()

    for cell in captions:
        mapped_name = name_mapping.get(cell.value.lower(), None)
        if mapped_name is not None:
            column_mapping[mapped_name] = cell.column

    return column_mapping
