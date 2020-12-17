from rest_framework import generics

from utils.api_logging import LoggingMixin
from utils.api_helpers import DefaultNameOrdering

from api.models import Kernel
from api.serializers import KernelFullSerializer


class KernelView(LoggingMixin, DefaultNameOrdering, generics.ListCreateAPIView):
    """
        get: List Kernel objects
        post: Create Kernel object
    """
    queryset = Kernel.objects.all()
    serializer_class = KernelFullSerializer
    filterset_fields = ['name']
