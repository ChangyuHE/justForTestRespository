from rest_framework import generics

from utils.api_logging import LoggingMixin
from utils.api_helpers import DefaultNameOrdering

from api.models import Driver
from api.serializers import DriverFullSerializer


class DriverView(LoggingMixin, DefaultNameOrdering, generics.ListCreateAPIView):
    """
        get: List Driver objects
        post: Create Driver object
    """
    queryset = Driver.objects.all()
    serializer_class = DriverFullSerializer
    filterset_fields = ['name']

