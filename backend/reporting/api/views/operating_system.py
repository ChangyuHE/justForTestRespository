from rest_framework import generics

from utils.api_logging import LoggingMixin
from utils.api_helpers import get_datatable_json, DefaultNameOrdering

from api.models import Os
from api.serializers import OsSerializer


class OsView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ List Os objects """
    queryset = Os.objects.all().prefetch_related('group')
    serializer_class = OsSerializer
    filterset_fields = {
        'name': ['exact'],
        'group__name': ['exact'],
        'weight': ['exact', 'gte', 'lte']
    }


class OsTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ Os table view formatted for DataTable """
    queryset = Os.objects.all()
    serializer_class = OsSerializer
    filterset_fields = {
        'name': ['exact'],
        'group__name': ['exact'],
        'weight': ['exact', 'gte', 'lte']
    }

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False, exclude=['group', 'weight'])
