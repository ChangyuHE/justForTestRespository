from collections import defaultdict

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from utils.api_helpers import get_datatable_json, UpdateWOutputAPIView, CreateWOutputApiView
from utils.api_logging import LoggingMixin

from api.models import FeatureMappingRule, TestScenario
from api.serializers import FeatureMappingSimpleRuleSerializer, FeatureMappingRuleSerializer

from .mapping import check_rules_conflicts


class FeatureMappingRulesConflictCheckView(LoggingMixin, APIView):
    """ Check for conflicts through mapping rules """
    def get(self, request, pk, *args, **kwargs):
        issues = defaultdict(list)
        rule_to_exclude = None

        # prepare data for edited/created rule
        new_ids = request.query_params.get('new_ids')
        if new_ids == 'none':
            new_ids = None
        scenario_id = request.query_params.get('scenario_id')

        # rule.id for edit or 'none' for new rule creation
        rule_id = request.query_params.get('rule_id')
        if rule_id != 'none':
            rule_to_exclude = rule_id

        scenario_name = TestScenario.objects.get(id=scenario_id).name
        rules = FeatureMappingRule.objects.filter(scenario_id=scenario_id, mapping_id=pk)
        # exclude ids for edited rule, because we passed new ones
        if rule_to_exclude:
            rules = rules.exclude(id=rule_to_exclude)

        # add new items to examine list
        ids_list = list(rules.values_list('ids', flat=True))
        ids_list.append(new_ids)

        issues = check_rules_conflicts(ids_list, scenario_name, issues)
        return Response(issues)

class FeatureMappingRuleDetailsView(
    LoggingMixin, generics.RetrieveDestroyAPIView, UpdateWOutputAPIView):
    """ FeatureMappingRule single object management """
    queryset = FeatureMappingRule.objects.all()
    serializer_class = FeatureMappingSimpleRuleSerializer
    serializer_output_class = FeatureMappingRuleSerializer


class FeatureMappingRuleView(LoggingMixin, generics.ListAPIView, CreateWOutputApiView):
    """
        get: List FeatureMappingRule objects according to filters
        post: Create FeatureMappingRule object using simple serializer, output with fill data
    """
    queryset = FeatureMappingRule.objects.all()
    serializer_output_class = FeatureMappingRuleSerializer
    filterset_fields = ['milestone', 'feature', 'scenario', 'mapping', 'total']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return FeatureMappingRuleSerializer
        return FeatureMappingSimpleRuleSerializer


class FeatureMappingRuleTableView(LoggingMixin, generics.ListAPIView):
    """ FeatureMappingRule table view formatted for DataTable """
    queryset = FeatureMappingRule.objects.all()
    serializer_class = FeatureMappingRuleSerializer
    filterset_fields = ['milestone', 'feature', 'scenario', 'mapping', 'total']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self)


