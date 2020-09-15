import logging

from django.db import transaction
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponse
from django.shortcuts import render

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.parsers import FileUploadParser

from datetime import datetime
from openpyxl import load_workbook, Workbook
from openpyxl.utils import get_column_letter as to_letter
from openpyxl.writer.excel import save_virtual_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

from api.models import FeatureMapping, FeatureMappingRule, Milestone, Feature, TestScenario
from api.forms import FeatureMappingFileForm
from api.serializers import FeatureMappingSimpleSerializer, FeatureMappingSerializer, FeatureMappingRuleSerializer, \
    FeatureMappingSimpleRuleSerializer, MilestoneSerializer, FeatureSerializer, TestScenarioSerializer
from test_verifier.models import Codec

from utils.api_logging import LoggingMixin
from utils.api_helpers import get_datatable_json, DefaultNameOrdering
from utils import api_helpers

log = logging.getLogger(__name__)


class FeatureMappingPostView(LoggingMixin, APIView):
    """ Excel file import view """
    parser_class = (FileUploadParser,)

    def post(self, request):
        if 'file' not in request.data:
            raise ParseError("'file' parameter is missing in form data.")

        fm_serializer = FeatureMappingSimpleSerializer(data=request.data)
        if not fm_serializer.is_valid():
            return Response({'errors': fm_serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        errors = import_feature_mapping(request.data['file'], fm_serializer)
        if errors:
            return Response({'errors': errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return Response(status=status.HTTP_201_CREATED)


class FeatureMappingListView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ List of available FeatureMappings filtered by owner/platform/os/component"""
    queryset = FeatureMapping.objects.all()
    serializer_class = FeatureMappingSerializer
    filterset_fields = ['name', 'owner', 'platform', 'os', 'component', 'public', 'official']


class FeatureMappingTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ FeatureMapping table view formatted for DataTable """
    queryset = FeatureMapping.objects.all()
    serializer_class = FeatureMappingSerializer
    filterset_fields = ['name', 'owner', 'platform', 'os', 'component', 'public', 'official']

    def get(self, request, *args, **kwargs):
        public = request.GET.get('public')
        exclude = []
        if not public:
            exclude = ['owner']
        return get_datatable_json(self, exclude=exclude)


class FeatureMappingDetailsView(LoggingMixin, generics.RetrieveDestroyAPIView, api_helpers.UpdateWOutputAPIView):
    """ FeatureMapping single object management """
    queryset = FeatureMapping.objects.all()
    serializer_class = FeatureMappingSimpleSerializer
    serializer_output_class = FeatureMappingSerializer


class FeatureMappingExportView(LoggingMixin, APIView):
    """ Export mapping as excel file """
    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if not pk:
            return Response({'details': 'no pk provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            mapping = FeatureMapping.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response({'details': f'Could not find mapping by id {pk}'}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'details': f'More than one objects found by id {pk}'}, status=status.HTTP_400_BAD_REQUEST)

        workbook = export_mapping(mapping)
        filename = f'FMT_{mapping.name}_{datetime.now():%Y-%m-%d_%H:%M:%S}.xlsx'
        response = HttpResponse(save_virtual_workbook(workbook), content_type="application/ms-excel")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


def export_mapping(mapping):
    wb = Workbook()
    ws = wb.active

    # first row (headers)
    for col, value in enumerate(('milestone', 'feature', 'scenario', 'ids'), start=1):
        ws.cell(row=1, column=col).value = value

    current_row = 2
    col_width = dict()
    # fill rows with data
    for values in FeatureMappingRule.objects.filter(mapping=mapping) \
            .values_list('milestone__name', 'feature__name', 'scenario__name', 'ids'):
        for col, value in enumerate(values, start=1):
            # collect max width per column
            col_width.setdefault(col, 0)
            if value and len(value) > col_width[col]:
                col_width[col] = len(value)

            ws.cell(row=current_row, column=col).value = value
        current_row += 1

    # set default column width
    for col_ind in col_width:
        ws.column_dimensions[to_letter(col_ind)].width = col_width[col_ind] + 3

    medium_style = TableStyleInfo(name='TableStyleMedium6', showRowStripes=True)

    table = Table(
        ref=f'A1:D{current_row - 1}', displayName='FMT', tableStyleInfo=medium_style)
    ws.add_table(table)

    return wb


# FeatureMapping Rules views

class FeatureMappingRuleDetailsView(LoggingMixin, generics.RetrieveDestroyAPIView, api_helpers.UpdateWOutputAPIView):
    """ FeatureMappingRule single object management """
    queryset = FeatureMappingRule.objects.all()
    serializer_class = FeatureMappingSimpleRuleSerializer
    serializer_output_class = FeatureMappingRuleSerializer


class FeatureMappingRuleView(LoggingMixin, generics.ListAPIView, api_helpers.CreateWOutputApiView):
    """
        get: List FeatureMappingRule objects according to filters
        post: Create FeatureMappingRule object using simple serializer, output with fill data
    """
    queryset = FeatureMappingRule.objects.all()
    serializer_output_class = FeatureMappingRuleSerializer
    filterset_fields = ['milestone', 'feature', 'scenario', 'mapping']
    ordering_fields = '__all__'
    ordering = ['milestone__name']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return FeatureMappingRuleSerializer
        return FeatureMappingSimpleRuleSerializer


class FeatureMappingRuleTableView(LoggingMixin, generics.ListAPIView):
    """ FeatureMappingRule table view formatted for DataTable """
    queryset = FeatureMappingRule.objects.all()
    serializer_class = FeatureMappingRuleSerializer
    filterset_fields = ['milestone', 'feature', 'scenario', 'mapping']
    ordering_fields = '__all__'
    ordering = ['milestone__name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self)


# Milestone views
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


# Feature views
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


# Scenario views
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


# for development needs
def feature_mapping_form(request):
    form = FeatureMappingFileForm()
    return render(request, 'api/feature_mapping_import.html', {'form': form})


def import_feature_mapping(file, serializer):
    errors = []
    data = serializer.data

    try:
        wb = load_workbook(file)
    except Exception as e:
        message = getattr(e, 'message', repr(e))
        log.warning(f'Failed to open workbook: {message}')
        errors.append({'workbook error': message})
        return errors

    sheet = wb[wb.sheetnames[0]]
    if sheet is None:
        errors.append({'workbook error': 'No sheets found'})
        return errors

    rows = sheet.rows
    if not rows:
        errors.append({'workbook format error': 'There must be 4 columns with "milestone", "feature", '
                                                '"scenario" and "ids" data (column headers do not matter)'})
        errors.append({'workbook error': 'No rows found'})
        return errors

    first_row = next(rows)
    headings = [c.value for c in first_row]
    if len(headings) != 4:
        errors.append(
            {'workbook format error': 'There must be 4 columns with "milestone", "feature", '
                                      '"scenario" and "ids" data (column headers do not matter)'})
        return errors

    fm_rules = []
    try:
        with transaction.atomic():
            mapping = FeatureMapping.objects.create(name=data['name'], owner_id=data['owner'], codec_id=data['codec'],
                                                    component_id=data['component'], platform_id=data['platform'],
                                                    os_id=data['os'])

            for i, row in enumerate(rows):
                milestone_name, feature_name, scenario_name, ids_value = [cell.value for cell in row]
                if all([milestone_name, feature_name, scenario_name]):
                    milestone, _ = Milestone.objects.get_or_create(name=milestone_name)
                    feature, _ = Feature.objects.get_or_create(name=feature_name)
                    scenario, _ = TestScenario.objects.get_or_create(name=scenario_name)

                    fm_rules.append(FeatureMappingRule(
                        mapping=mapping, milestone=milestone, feature=feature, scenario=scenario,
                        ids=ids_value if ids_value else None
                    ))
                else:
                    errors.append({f'workbook error (row {i + 2})': 'Empty cell'})
            FeatureMappingRule.objects.bulk_create(fm_rules)
    except IntegrityError as e:
        errors.append({'import error': f'Integrity error: {e.__cause__}'})

    return errors
