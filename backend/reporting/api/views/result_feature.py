from rest_framework import generics

from utils.api_logging import LoggingMixin
from utils.api_helpers import get_datatable_json, DefaultNameOrdering

from api.models import ResultFeature
from api.serializers import ResultFeatureSerializer

from .filters import ResultFeatureFilter


class ResultFeatureView(LoggingMixin, generics.ListAPIView):
    """ List of ResultFeature objects """
    queryset = ResultFeature.objects.all()
    serializer_class = ResultFeatureSerializer
    filterset_class = ResultFeatureFilter
