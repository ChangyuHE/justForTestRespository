from rest_framework import generics

from utils.api_logging import LoggingMixin

from api.models import Simics
from api.serializers import SimicsSerializer


class SimicsView(LoggingMixin, generics.ListCreateAPIView):
    """ List of Simics objects """
    queryset = Simics.objects.all()
    serializer_class = SimicsSerializer

