from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict
from typing import Any

from utils import api_logging
from django.utils import timezone
from django.db.models import Model
from django.contrib.auth.models import User

from api import models as api_models
from api.collate.excel_utils import SheetMapping


class RequestDTO:
    file: 'django.core.files.File'
    validation_id: int
    name: str
    notes: str
    date: Any
    source_file: str
    force_run: bool
    requester: User
    site_url: str

    def __str__(self):
        return f"RequestDTO: {self.__dict__}"

    @staticmethod
    def build(request) -> 'RequestDTO':
        dto = RequestDTO()

        dto.file = RequestDTO.__get_field(request, 'file')
        dto.validation_id = RequestDTO.__extract_validation_id(request)
        dto.name = RequestDTO.__get_field(request, 'validation_name')
        dto.notes = RequestDTO.__get_field(request, 'notes')
        dto.date = RequestDTO.__extract_date(request)
        dto.source_file = RequestDTO.__get_field(request, 'source_file')
        dto.force_run = RequestDTO.__extract_force_run(request)
        dto.requester = api_logging.get_user_object(request)
        dto.site_url = request.build_absolute_uri('/')

        return dto

    @staticmethod
    def __get_field(request, field_name, fallback_value=None):
        if request is None:
            return fallback_value

        return request.data.get(field_name, fallback_value)

    @staticmethod
    def __extract_validation_id(request):
        validation_id = RequestDTO.__get_field(request, 'validation_id')

        if str(validation_id).strip() == '':
            validation_id = None

        return validation_id

    @staticmethod
    def __extract_date(request):
        date = RequestDTO.__get_field(request, 'validation_date')

        if str(date).strip() == '':
            date = None

        if date is None:
            date = timezone.make_aware(datetime.now())

        return date

    @staticmethod
    def __extract_force_run(request):
        force_run = RequestDTO.__get_field(request, 'force_run', False)

        return force_run in [True, 'True', 'on', 'true']


@dataclass
class ValidationDTO:
    id: int = None
    name: str = ''
    env_id: int = None
    platform_id: int = None
    os_id: int = None
    notes: str = None
    date: str = None
    source_file: str = None
    owner_id: int = None

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def build(validation: api_models.Validation) -> 'ValidationDTO':
        dto = ValidationDTO()

        dto.id = validation.id
        dto.name = validation.name
        dto.env_id = validation.env.id if validation.env else None
        dto.platform_id = validation.platform.id if validation.platform else None
        dto.os_id = validation.os.id if validation.os else None
        dto.notes = validation.notes
        dto.date = str(validation.date) if validation.date else None
        dto.source_file = validation.source_file
        dto.owner_id = validation.owner.id if validation.owner else None

        return dto

    def to_validation(self):
        if self.id:
            return api_models.Validation.objects.filter(pk=self.id).first()

        validation = api_models.Validation()
        validation.name = self.name
        validation.env = api_models.Env.objects.get(pk=self.env_id)
        validation.platform = api_models.Platform.objects.get(pk=self.platform_id)
        validation.os = api_models.Os.objects.get(pk=self.os_id)
        validation.notes = self.notes
        validation.date = self.date
        validation.source_file = self.source_file
        validation.owner = User.objects.filter(pk=self.owner_id).first()

        return validation


class OutcomeBuilder:
    def __init__(self):
        self.success = False
        self.errors = []
        self.warnings = defaultdict(int)
        self.changes = dict(added=0, updated=0, skipped=0)
        self.job_id = None

    def build(self):
        outcome = {}
        success = self.is_success()
        if success:
            outcome = dict(
                success=success,
                job_id=self.job_id,
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
        self.warnings[warning] += 1

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


class Context:
    request: RequestDTO = None
    validation: api_models.Validation = None
    outcome: OutcomeBuilder
    mapping: SheetMapping

    def __init__(self):
        self.outcome = OutcomeBuilder()
        self.mapping = SheetMapping()

    def save_transient_validation(self):
        if self.validation is not None and self.validation.pk is None:
            self.validation.save()

    def get_validation_id(self):
        return self.validation.id if self.validation else None


@dataclass
class ResultMandatoryData:
    validation: api_models.Validation = None
    env: api_models.Env = None
    component: api_models.Component = None
    item: api_models.Item = None
    status: api_models.Status = None
    platform: api_models.Platform = None
    os: api_models.Os = None
    run: api_models.Run = None

    def is_valid(self):
        return None not in self.__dict__.values()


@dataclass
class ResultExtraData:
    driver: api_models.Driver = None
    scenario_asset: api_models.ScenarioAsset = None
    msdk_asset: api_models.MsdkAsset = None
    os_asset: api_models.OsAsset = None
    lucas_asset: api_models.LucasAsset = None
    fulsim_asset: api_models.FulsimAsset = None
    simics: api_models.Simics = None
    additional_parameters: Any = None


class ResultData:
    mandatory: ResultMandatoryData
    extra: ResultExtraData

    def __init__(self):
        self.mandatory = ResultMandatoryData()
        self.extra = ResultExtraData()

    def get_fields(self):
        # dataclasses.asdict(..) uses deep object copy instead of object reference
        fields = dict(self.mandatory.__dict__)
        fields.update(self.extra.__dict__)

        return fields

    def save_transient(self, cache: 'ObjectsCache'):
        for entity in self.get_fields().values():
            if issubclass(type(entity), Model) and entity.id is None:
                entity.save()
                cache.update(entity.__class__, entity.id)

    def update_model(self, model: api_models.Result):
        for name, value in self.get_fields().items():
            setattr(model, name, value)
