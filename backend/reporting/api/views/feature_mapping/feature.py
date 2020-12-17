from rest_framework import generics

from utils.api_helpers import get_datatable_json, DefaultNameOrdering
from utils.api_logging import LoggingMixin

from api.models import Feature
from api.serializers import FeatureSerializer


class FeatureMappingFeatureView(LoggingMixin, DefaultNameOrdering, generics.ListCreateAPIView):
    """
        get: List FeatureMapping Feature objects according to filters
        post: Create FeatureMapping Feature object
    """
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    filterset_fields = ['name']


class FeatureMappingFeatureDetailsView(LoggingMixin, generics.RetrieveUpdateDestroyAPIView):
    """ FeatureMapping Feature single object management """
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer


class FeatureMappingFeatureTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ FeatureMapping Feature table view formatted for DataTable """
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self)
