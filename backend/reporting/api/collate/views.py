import logging

from django.shortcuts import render

from .business_entities import ImportRequestDTO, CloneRequestDTO
from .business_entities import MergeRequestDTO
from .clone_api import clone_validations
from .forms import SelectFileForm
from .import_api import EntityException
from .import_api import import_results
from .import_api import create_entities
from .merge_api import merge_validations

from rest_framework.exceptions import ParseError
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from api.views import LoggingMixin

log = logging.getLogger(__name__)


def _get_status_code(outcome):
        return status.HTTP_200_OK if outcome.is_success() else status.HTTP_422_UNPROCESSABLE_ENTITY


def index(request):
    form = SelectFileForm()
    return render(request, 'collate/index.html', {'form': form})


class ImportFileView(LoggingMixin, APIView):
    parser_class = (FileUploadParser,)

    def post(self, request):
        log.debug('Processing POST request in ImportFileView')
        self.__validate_request(request)

        request_dto = ImportRequestDTO.build(request)
        outcome = import_results(request_dto)
        log.debug('Request was processed without exceptions.')

        data = outcome.build()
        code = _get_status_code(outcome)
        log.debug(f"Returning '{code}' status code.")

        return Response(data=data, status=code)

    def __validate_request(self, request):
        log.debug(f'request data: {request.data}')

        if 'file' not in request.data:
            raise ParseError("'file' parameter is missing in form data.")


class CreateEntitiesView(LoggingMixin, APIView):
    def post(self, request):
        log.debug(f'request data: {request.data}')
        if 'entities' not in request.data:
            raise ParseError("'entities' parameter is missing in request.")

        entities = request.data['entities']

        try:
            create_entities(entities)
        except EntityException as e:
            raise ParseError(e)

        return Response(status=status.HTTP_201_CREATED)


class MergeValidationsView(LoggingMixin, APIView):
    def post(self, request):
        log.debug(f'request data: {request.data}')

        dto = MergeRequestDTO.build(request)
        outcome = merge_validations(dto)
        code = _get_status_code(outcome)

        return Response(data=outcome.build(), status=code)


class CloneValidationsView(LoggingMixin, APIView):
    def post(self, request):
        log.debug(f'request data: {request.data}')

        dto = CloneRequestDTO.build(request)
        outcome = clone_validations(dto)
        code = _get_status_code(outcome)

        return Response(data=outcome.build(), status=code)
