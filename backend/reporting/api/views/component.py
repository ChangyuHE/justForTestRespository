from rest_framework import generics

from utils.api_logging import LoggingMixin
from utils.api_helpers import get_datatable_json, DefaultNameOrdering

from api.models import Component
from api.serializers import ComponentSerializer

from .filters import ComponentFilter


class ComponentView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ List of Component objects """
    queryset = Component.objects.all()
    serializer_class = ComponentSerializer
    filterset_class = ComponentFilter


class ComponentTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ Component table view formatted for DataTable """
    queryset = Component.objects.all()
    serializer_class = ComponentSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False)
