from rest_framework import generics

from utils.api_logging import LoggingMixin

from api.models import Status
from api.serializers import StatusFullSerializer

from .filters import StatusFilter


class StatusView(LoggingMixin, generics.ListAPIView):
    """ List of Status objects """
    queryset = Status.objects.all()
    serializer_class = StatusFullSerializer
    filterset_class = StatusFilter
