import logging

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import reverse

from .forms import SelectFileForm
from .services import import_results
from .services import create_entities
from .services import EntityException

from rest_framework.exceptions import ParseError
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

log = logging.getLogger(__name__)


def index(request):
    form = SelectFileForm()
    return render(request, 'collate/index.html', {'form': form})


class ImportFileView(APIView):
    parser_class = (FileUploadParser,)

    def post(self, request):
        log.debug('Processing POST request in ImportFileView')

        if 'file' not in request.data:
            raise ParseError("'file' parameter is missing in form data.")

        file = request.data['file']
        validation_id = request.data.get('validation_id')

        outcome = import_results(file, validation_id)

        log.debug('About to return Response.')
        data = outcome.build()
        code = status.HTTP_200_OK if outcome.success else status.HTTP_422_UNPROCESSABLE_ENTITY

        return Response(data=data, status=code)


class CreateEntitiesView(APIView):
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
