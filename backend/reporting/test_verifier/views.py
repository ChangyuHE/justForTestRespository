from openpyxl import load_workbook
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.views import APIView

from api.views import LoggingMixin

from .services import import_features


class ImportView(LoggingMixin, APIView):
    def post(self, request):
        if 'file' not in request.data:
            raise ParseError("'file' parameter is missing in form data.")
        file = request.data['file']
        outcome = import_features(file)

        data = outcome.build()
        code = status.HTTP_200_OK if outcome.is_success() else status.HTTP_422_UNPROCESSABLE_ENTITY

        return Response(data=data, status=code)
