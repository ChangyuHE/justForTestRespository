import logging

from django.shortcuts import render

from .forms import SelectFileForm
from .services import import_results
from .services import create_entities
from .services import EntityException
from .services import ImportDescriptor

from rest_framework.exceptions import ParseError
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from api.views import LoggingMixin

log = logging.getLogger(__name__)


def index(request):
    form = SelectFileForm()
    return render(request, 'collate/index.html', {'form': form})


class ImportFileView(LoggingMixin, APIView):
    parser_class = (FileUploadParser,)

    def post(self, request):
        log.debug('Processing POST request in ImportFileView')

        if 'file' not in request.data:
            raise ParseError("'file' parameter is missing in form data.")

        file = request.data['file']
        descriptor = ImportDescriptor(
            request.data.get('validation_id', None),
            request.data.get('validation_name', None),
            request.data.get('validation_date', None),
            request.data.get('notes', None),
            request.data.get('source_file', None),
            request.data.get('force_run', False),
        )

        log.debug(f'request data: {request.data}')

        outcome = import_results(file, descriptor, request)

        log.debug('About to return Response.')
        data = outcome.build()
        code = status.HTTP_200_OK if outcome.is_success() else status.HTTP_422_UNPROCESSABLE_ENTITY

        return Response(data=data, status=code)


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
