import time
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from typing import Any
from typing import List

from utils import api_logging
from django.utils import timezone
from django.db.models import Model
from django.contrib.auth.models import User
from django.core.files import File

from api import models as api_models
from api.collate.excel_utils import SheetMapping


class AbstractRequestDTO(ABC):
    def __str__(self):
        return f"{self.__class__.__name__}: {self.__dict__}"

    @staticmethod
    def _get_field(request, field_name, fallback_value=None):
        if request is None:
            return fallback_value

        return request.data.get(field_name, fallback_value)

    @staticmethod
    def _get_list(request, field_name, fallback_value=None):
        if fallback_value is None:
            fallback_value = []
        # request.data is a dict when the it is comes from frontend
        if isinstance(request.data, dict):
            return request.data[field_name]
        # request.data can be a QueryDict when it is comes from raw api call
        return request.data.getlist(field_name, fallback_value)

    @classmethod
    def _extract_boolean(cls, request, field):
        value = cls._get_field(request, field, False)

        return value in [True, 'True', 'on', 'true']


class ImportRequestDTO(AbstractRequestDTO):
    file: File
    is_url_import: bool
    validation_id: int
    name: str
    notes: str
    date: Any
    source_file: str
    force_run: bool
    requester: User
    site_url: str
    force_item: bool
    import_reason: str

    @classmethod
    def build(cls, request) -> 'ImportRequestDTO':
        dto = cls()

        dto.file = cls._get_field(request, 'file')
        dto.is_url_import = cls._extract_boolean(request, 'is_url_import')
        dto.validation_id = cls.__extract_validation_id(request)
        dto.name = cls._get_field(request, 'validation_name')
        dto.notes = cls._get_field(request, 'notes')
        dto.date = cls.__extract_date(request)
        dto.source_file = cls._get_field(request, 'source_file')
        dto.force_run = cls._extract_boolean(request, 'force_run')
        dto.requester = api_logging.get_user_object(request)
        dto.site_url = request.build_absolute_uri('/')
        dto.force_item = cls._extract_boolean(request, 'force_item')
        dto.import_reason = cls._get_field(request, 'import_reason')

        return dto

    @classmethod
    def __extract_validation_id(cls, request):
        validation_id = cls._get_field(request, 'validation_id')

        if str(validation_id).strip() == '':
            validation_id = None

        return validation_id

    @classmethod
    def __extract_date(cls, request):
        date = cls._get_field(request, 'validation_date', fallback_value='')

        if str(date).strip() == '':
            date = datetime.now()
        else:
            date = datetime(*time.strptime(date, '%Y-%m-%d')[:6])

        # always return datetime with TZ set to ensure we have
        # no warning on validation save
        return timezone.make_aware(date)


class MergeRequestDTO(AbstractRequestDTO):
    requester: User
    validation_name: str
    notes: str
    validation_ids: List[int]
    site_url: str
    strategy: str

    @classmethod
    def build(cls, request) -> 'MergeRequestDTO':
        dto = cls()

        dto.requester = api_logging.get_user_object(request)
        dto.validation_name = cls._get_field(request, 'validation_name', fallback_value='')
        dto.notes = cls._get_field(request, 'notes')
        dto.validation_ids = cls._get_list(request, 'validation_ids')
        dto.site_url = request.build_absolute_uri('/')
        dto.strategy = cls.__get_strategy(request)

        return dto

    @classmethod
    def __get_strategy(cls, request):
        available_strategies = ['best', 'last']
        default_strategy = available_strategies[0]

        strategy = str(cls._get_field(request, 'strategy', default_strategy)).lower()
        if strategy not in available_strategies:
            strategy = default_strategy

        return strategy

    def validation_name_missed(self):
        return not bool(self.validation_name.strip())


class CloneRequestDTO(AbstractRequestDTO):
    requester: User
    validation_name: str
    notes: str
    validation_id: int
    site_url: str

    @classmethod
    def build(cls, request) -> 'CloneRequestDTO':
        dto = cls()

        dto.requester = api_logging.get_user_object(request)
        dto.validation_name = cls._get_field(request, 'validation_name', fallback_value='')
        dto.notes = cls._get_field(request, 'notes')
        dto.validation_id = cls._get_field(request, 'validation_id')
        dto.site_url = request.build_absolute_uri('/')

        return dto

    def validation_name_missed(self):
        return not bool(self.validation_name.strip())


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
            return api_models.Validation.alive_objects.filter(pk=self.id).first()

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


class AbstractOutcomeBuilder(ABC):
    def __init__(self):
        self.success = False
        self.errors = []
        self.warnings = defaultdict(int)
        self.job_id = None

        self.success_fields = ['success', 'job_id']
        self.failure_fields = ['success', 'errors', 'warnings']

    def build(self):
        outcome = {}
        self.success = self.is_success()

        field_names = self.success_fields if self.success else self.failure_fields
        for field in field_names:
            outcome[field] = getattr(self, field)

        return outcome

    def is_success(self):
        return len(self.errors) + len(self.warnings) == 0

    def add_warning(self, warning):
        self.warnings[warning] += 1

    def _add_error(self, code, message, **kwargs):
        err = dict(code=code, message=message, **kwargs)
        if err not in self.errors:
            self.errors.append(err)

    def add_ambiguous_column_error(self, column, values):
        message = 'Two or more distinct values in column'
        self._add_error('ERR_AMBIGUOUS_COLUMN', message, column=column, values=values)

    def add_existing_validation_error(self, message, fields_data):
        fields = {str(key): str(value) for (key, value) in fields_data}
        entity = dict(model='Validation', fields=fields)

        self._add_error('ERR_EXISTING_VALIDATION', message, entity=entity)

    def add_validation_name_error(self):
        message = 'Missing or empty validation name.'
        self._add_error('ERR_EMPTY_VALIDATION_NAME', message)

    def add_nonexistent_validation_error(self):
        message = 'Non-existent validation id'
        self._add_error('ERR_NONEXISTENT_VALIDATION_ID', message)


class ImportOutcomeBuilder(AbstractOutcomeBuilder):
    def __init__(self):
        super().__init__()
        self.changes = dict(added=0, updated=0, skipped=0)
        self.success_fields.append('changes')

    def add_invalid_validation_error(self, message):
        self._add_error('ERR_INVALID_VALIDATION_ID', message)

    def add_missing_field_error(self, missing_field, is_alias=False):
        model_name, fields = missing_field
        entity=dict(model=model_name, fields=fields)

        if is_alias:
            self.add_warning(f"{model_name} with name or alias '{fields['name']}' does not exist.")
        else:
            self.add_warning(f'{model_name} with properties {fields} does not exist.')

        self._add_error('ERR_MISSING_ENTITY', f'Missing field {missing_field}', entity=entity)

    def add_missing_columns_error(self, columns):
        message = 'Not all columns found, please check import file for correctness.'
        self._add_error('ERR_MISSING_COLUMNS', message, values=columns)

    def add_workbook_error(self, message):
        self._add_error('ERR_WORKBOOK_EXCEPTION', message)

    def add_existing_run_error(self, run):
        message = f"Run with name '{run.name}' and session '{run.session}' already exist."
        self.add_warning(message)
        self._add_error('ERR_EXISTING_RUN', message)

    def add_date_format_error(self, date, field_type='string'):
        message=f'Unable to auto-convert {field_type} "{date}" to excel date.'
        self._add_error('ERR_DATE_FORMAT', message)

    def add_item_changed_error(self, item, old_status, new_status):
        if old_status != new_status:
            message = f"Result changed from '{old_status}' to '{new_status}'"
        else:
            message = f"Changed Result with '{new_status}' status"

        code = 'ERR_ITEM_CHANGED'
        suite_name = item.scenario.name if item.scenario else item.name

        for err in self.errors:
            if err['code'] == code and err['message'] == message:
                if item.test_id is not None:
                    err['details'][suite_name].append(item.test_id)
                break
        else:
            details = defaultdict(list)

            if item.test_id is not None:
                details[suite_name] = [item.test_id]
            else:
                details[suite_name] = []

            self._add_error(code, message, details=details)

        self.add_warning(message)


class MergeOutcomeBuilder(AbstractOutcomeBuilder):
    def add_validation_list_error(self):
        message = 'List of validations must contain at least 2 items.'
        self._add_error('ERR_VALIDATION_LIST', message)


class CloneOutcomeBuilder(AbstractOutcomeBuilder):
    def add_selected_validation_error(self):
        message = 'Missing validation.'
        self._add_error('ERR_EMPTY_VALIDATION', message)

    def add_duplicated_validation_error(self):
        message = 'Duplicate validation name.'
        self._add_error('ERR_DUPLICATE_VALIDATION', message)


class Context:
    request: ImportRequestDTO = None
    validation: api_models.Validation = None
    outcome: ImportOutcomeBuilder
    mapping: SheetMapping

    def __init__(self):
        self.outcome = ImportOutcomeBuilder()
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
    features: List[api_models.ResultFeature] = field(default_factory=list)
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
    kernel: api_models.Kernel = None
    lucas_asset: api_models.LucasAsset = None
    fulsim_asset: api_models.FulsimAsset = None
    simics: api_models.Simics = None
    additional_parameters: Any = None
    test_error: str = None
    scenario_url: str = None


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
