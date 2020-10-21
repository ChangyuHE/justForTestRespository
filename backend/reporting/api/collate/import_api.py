import logging

from django.core.files.storage import default_storage

from api.collate.business_entities import Context
from api.collate.business_entities import ValidationDTO
from api.collate.services import verify_file
from api.collate.services import get_temp_name
from api.serializers import create_serializer
from api.models import ImportJob
from api.collate.tasks.task_import import do_import

log = logging.getLogger(__name__)


def import_results(request_dto):
    context = Context()
    context.request = request_dto

    # check if file can be imported
    verify_file(context)

    if context.outcome.is_success():
        # store file content
        _store_results(context)

    return context.outcome


def _store_results(context):
    tmp_name = get_temp_name()
    with default_storage.open(tmp_name, 'wb+') as destination:
        for chunk in context.request.file.chunks():
            destination.write(chunk)

    obj = ImportJob.objects.create(
        path=tmp_name,
        requester=context.request.requester,
        force_run=context.request.force_run,
        force_item=context.request.force_item,
        site_url=context.request.site_url,
    )
    validation_dto = ValidationDTO.build(context.validation)

    # Start background part of import
    do_import.send(obj.id, validation_dto.to_dict(), context.request.import_reason)
    context.outcome.job_id = obj.id


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


class EntityException(Exception):
    pass
