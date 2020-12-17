from rest_framework import generics

from utils.api_logging import LoggingMixin
from utils.api_helpers import get_datatable_json, DefaultNameOrdering

from api.models import Env
from api.serializers import EnvSerializer


class EnvView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ List Env objects """
    queryset = Env.objects.all()
    serializer_class = EnvSerializer
    filterset_fields = ['name']


class EnvTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ Env table view formatted for DataTable """
    queryset = Env.objects.all()
    serializer_class = EnvSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False)
