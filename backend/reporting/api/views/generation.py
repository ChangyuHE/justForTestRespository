from rest_framework import generics

from utils.api_logging import LoggingMixin
from utils.api_helpers import get_datatable_json, DefaultNameOrdering

from api.models import Generation
from api.serializers import GenerationSerializer


class GenerationView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ List Generation objects """
    queryset = Generation.objects.all()
    serializer_class = GenerationSerializer
    filterset_fields = ['name']


class GenerationTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ Generation table view formatted for DataTable """
    queryset = Generation.objects.all()
    serializer_class = GenerationSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False)
