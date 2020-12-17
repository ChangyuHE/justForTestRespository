from rest_framework import generics
from rest_framework.response import Response

from utils.api_logging import LoggingMixin
from utils.api_helpers import get_datatable_json, DefaultNameOrdering

from api.models import ValidationType, DEFAULT_VAL_TYPE_NAME
from api.serializers import ValidationTypeSerializer


class ValidationTypeView(LoggingMixin, generics.ListAPIView):
    """ List of ValidationType objects """
    queryset = ValidationType.objects.all()
    serializer_class = ValidationTypeSerializer
    filterset_fields = ['name']


class ValidationTypeDetailsView(LoggingMixin, generics.RetrieveUpdateAPIView):
    """ ValidationType single object management """
    queryset = ValidationType.objects.all()
    serializer_class = ValidationTypeSerializer
    filterset_fields = ['name']


class ValidationTypeTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ ValidationType table view formatted for DataTable """
    queryset = ValidationType.objects.all()
    serializer_class = ValidationTypeSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self)


class ValidationTypeWithDefaultView(LoggingMixin, generics.ListAPIView):
    """ List of ValidationType objects and default validation type name
        return: {'items': [all_valtypes], 'default': DEFAULT_VAL_TYPE_NAME}
    """
    queryset = ValidationType.objects.all()
    serializer_class = ValidationTypeSerializer
    filterset_fields = ['name']

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = ValidationTypeSerializer(queryset, many=True)
        return Response({'items': serializer.data, 'default': DEFAULT_VAL_TYPE_NAME})
