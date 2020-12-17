from rest_framework import generics

from utils.api_logging import LoggingMixin
from utils.api_helpers import get_datatable_json, DefaultNameOrdering

from api.models import Platform
from api.serializers import PlatformSerializer


class PlatformView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ List Platform objects """
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    filterset_fields = ['name', 'short_name', 'generation__name']


class PlatformTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ Platform table view formatted for DataTable """
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    filterset_fields = ['name', 'short_name', 'generation__name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False, exclude=['planning', 'weight'])
