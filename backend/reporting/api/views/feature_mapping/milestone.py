from rest_framework import generics

from utils.api_helpers import get_datatable_json, DefaultNameOrdering
from utils.api_logging import LoggingMixin

from api.models import Milestone
from api.serializers import MilestoneSerializer


class FeatureMappingMilestoneView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ List FeatureMapping Milestone objects """
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    filterset_fields = ['name']


class FeatureMappingMilestoneDetailsView(LoggingMixin, generics.RetrieveUpdateDestroyAPIView):
    """ FeatureMapping Milestone single object management """
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer


class FeatureMappingMilestoneTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ FeatureMapping Milestone table view formatted for DataTable """
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False)
