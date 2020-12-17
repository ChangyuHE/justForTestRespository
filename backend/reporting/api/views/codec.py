from rest_framework import generics

from utils.api_logging import LoggingMixin
from utils.api_helpers import get_datatable_json, DefaultNameOrdering

from test_verifier.models import Codec
from test_verifier.serializers import CodecSerializer


class CodecView(LoggingMixin, DefaultNameOrdering, generics.ListCreateAPIView):
    """
        get: List Codec objects
        post: Create Codec object
    """
    queryset = Codec.objects.all()
    serializer_class = CodecSerializer
    filterset_fields = ['name']


class CodecDetailsView(LoggingMixin, generics.RetrieveUpdateDestroyAPIView):
    """ Codec single object management """
    queryset = Codec.objects.all()
    serializer_class = CodecSerializer
    filterset_fields = ['name']


class CodecTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ Codec table view formatted for DataTable """
    queryset = Codec.objects.all()
    serializer_class = CodecSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self)
