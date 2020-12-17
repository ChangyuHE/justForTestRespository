import json
import logging

import requests
from requests.auth import HTTPBasicAuth

from django.conf import settings
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


class ParseShortUrlView(LoggingMixin, APIView):
    """Parse full Comparison View url location from its short version"""

    def post(self, request):
        short_url: str = request.data['short_url']
        if 'https' in short_url:
            # change to HTTP and related port to skip ssl verification
            short_url = short_url.replace('https://gta.intel.com/', 'http://gta.intel.com:80/')
        r = requests.get(short_url, allow_redirects=False,
                         auth=HTTPBasicAuth(settings.GTA_API_USER,
                                            settings.GTA_API_PASSWORD))
        if r.status_code == 302:
            return Response(data=r.headers['Location'], status=status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND)


class CheckTestRunExist(LoggingMixin, APIView):
    """Send request to GTA Results API to check that manually added
       Test Run ID contains any results
    """

    def post(self, request):
        test_run: str = request.data['test_run'][0]

        # use minimum possible payload to check existence of results for specific test run
        payload = {
            'globalFilterId': None,
            'compareOn': [
                'compareIdentifier',
            ],
            'filterGroups': [{
                'mode': 'DNF',
                'filters': [
                    {
                        'testRun':
                            [test_run],
                        'tagsExcept': [
                            'notAnIssue',
                            'obsoleted',
                            'iteration',
                            'isolation',
                        ]
                    }
                ],
                'customColumnsFilters': {}
            }],
            'diffOnly': False,
            'skipMissing': False,
            'grouped': True,
            'columns': [
                'itemName',
                'args',
            ],
        }
        # this request has limit just to 3 test items (..&limit=3), to get results response quickly
        r = requests.post('http://gta.intel.com:80/api/results/v2/results?offset=0&limit=3',
                          data=json.dumps(payload),
                          headers={
                              'Accept': 'application/json',
                              'Content-Type': 'application/json'
                          },
                          auth=HTTPBasicAuth(settings.GTA_API_USER,
                                             settings.GTA_API_PASSWORD))
        if r.status_code == 200:
            # check number of items in response data
            items_data = json.loads(r.content)['items']

            # at least one test result exists
            if items_data:
                items_data = {'items': items_data}
                return Response(data=items_data, status=status.HTTP_200_OK)
            else:
                # if it returns empty dict in items - no results
                items_data = {'items': []}
                return Response(data=items_data, status=status.HTTP_200_OK)
        return Response(data=r.content, status=r.status_code)

