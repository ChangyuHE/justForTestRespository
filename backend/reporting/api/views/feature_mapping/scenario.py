from rest_framework import generics

from utils.api_helpers import get_datatable_json, DefaultNameOrdering
from utils.api_logging import LoggingMixin

from api.models import TestScenario
from api.serializers import TestScenarioSerializer


class FeatureMappingScenarioView(LoggingMixin, DefaultNameOrdering, generics.ListCreateAPIView):
    """
        get: List FeatureMapping Test Scenario objects according to filters
        post: Create FeatureMapping Test Scenario object
    """
    queryset = TestScenario.objects.all()
    serializer_class = TestScenarioSerializer
    filterset_fields = ['name']


class FeatureMappingScenarioDetailsView(LoggingMixin, generics.RetrieveUpdateDestroyAPIView):
    """ FeatureMapping Test Scenario single object management """
    queryset = TestScenario.objects.all()
    serializer_class = TestScenarioSerializer


class FeatureMappingScenarioTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ FeatureMapping Test Scenario table view formatted for DataTable """
    queryset = TestScenario.objects.all()
    serializer_class = TestScenarioSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self)
