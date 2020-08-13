import logging

import django_filters.rest_framework
from django.db import transaction
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponse
from django.shortcuts import render

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from rest_framework.parsers import FileUploadParser

from datetime import datetime
from openpyxl import load_workbook, Workbook
from openpyxl.utils import get_column_letter as to_letter
from openpyxl.writer.excel import save_virtual_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo


from api.models import FeatureMapping, FeatureMappingRule, Milestone, Feature, TestScenario
from api.forms import FeatureMappingFileForm
from api.serializers import *

from utils.api_logging import LoggingMixin
from utils.api_helpers import get_datatable_json


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


class FeatureMappingListView(LoggingMixin, generics.ListAPIView):
    """ List of available FeatureMappings filtered by owner/platform/os/component"""
    queryset = FeatureMapping.objects.all()
    serializer_class = FeatureMappingSerializer
    filterset_fields = ['owner', 'platform', 'os', 'component', 'public', 'official']


class FeatureMappingDetailsTableView(LoggingMixin, generics.ListAPIView):
    queryset = FeatureMapping.objects.all()
    serializer_class = FeatureMappingSerializer
    filterset_fields = ['owner', 'platform', 'os', 'component', 'public', 'official']

    def get(self, request, *args, **kwargs):
        public = request.GET.get('public')
        exclude = []
        if not public:
            exclude = ['owner']
        return get_datatable_json(self, exclude=exclude)


class FeatureMappingUpdateView(LoggingMixin, generics.UpdateAPIView):
    queryset = FeatureMapping.objects.all()
    serializer_class = FeatureMappingSimpleSerializer


class FeatureMappingDeleteView(LoggingMixin,  generics.DestroyAPIView):
    queryset = FeatureMapping.objects.all()
    serializer_class = FeatureMappingSerializer


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
    for col, value in enumerate(('milestone', 'feature', 'scenario'), start=1):
        ws.cell(row=1, column=col).value = value

    current_row = 2
    col_width = dict()
    # fill rows with data
    for values in FeatureMappingRule.objects.filter(mapping=mapping) \
            .values_list('milestone__name', 'feature__name', 'scenario__name'):
        for col, value in enumerate(values, start=1):
            # collect max width per column
            col_width.setdefault(col, 0)
            if len(value) > col_width[col]:
                col_width[col] = len(value)

            ws.cell(row=current_row, column=col).value = value
        current_row += 1

    # set default column width
    for col_ind in col_width:
        ws.column_dimensions[to_letter(col_ind)].width = col_width[col_ind] + 2

    medium_style = TableStyleInfo(name='TableStyleMedium6', showRowStripes=True)

    table = Table(
        ref=f'A1:C{current_row - 1}', displayName='FMT', tableStyleInfo=medium_style)
    ws.add_table(table)

    return wb


# FeatureMapping Rules views

class FeatureMappingRuleDetailsView(LoggingMixin, generics.ListAPIView):
    """ Get details about FeatureMappingRules according to provided filters """
    queryset = FeatureMappingRule.objects.all()
    serializer_class = FeatureMappingRuleSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['milestone', 'feature', 'scenario', 'mapping']
    ordering_fields = '__all__'
    ordering = ['milestone']


class FeatureMappingRuleCreateView(LoggingMixin, generics.CreateAPIView):
    queryset = FeatureMappingRule.objects.all()
    serializer_class = FeatureMappingSimpleRuleSerializer


class FeatureMappingRuleUpdateView(LoggingMixin, generics.UpdateAPIView):
    queryset = FeatureMappingRule.objects.all()
    serializer_class = FeatureMappingSimpleRuleSerializer


class FeatureMappingRuleDeleteView(LoggingMixin,  generics.DestroyAPIView):
    """ Delete specified rule from FeatureMappingRules table """
    queryset = FeatureMappingRule.objects.all()
    serializer_class = FeatureMappingRuleSerializer


class FeatureMappingRuleDetailsTableView(LoggingMixin, generics.ListAPIView):
    """ Rules table view formatted for DataTable """
    queryset = FeatureMappingRule.objects.all()
    serializer_class = FeatureMappingRuleSerializer
    filterset_fields = ['milestone', 'feature', 'scenario', 'mapping']
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = '__all__'
    ordering = ['milestone']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self)


# Milestone views
class FeatureMappingMilestoneView(LoggingMixin, generics.ListCreateAPIView):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    filterset_fields = ['name']


class FeatureMappingMilestoneDetailsView(LoggingMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer


class FeatureMappingMilestoneTableView(LoggingMixin, generics.ListAPIView):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False)


# Feature views
class FeatureMappingFeatureView(LoggingMixin, generics.ListCreateAPIView):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    filterset_fields = ['name']


class FeatureMappingFeatureDetailsView(LoggingMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer


class FeatureMappingFeatureTableView(LoggingMixin, generics.ListCreateAPIView):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self)


# Scenario views
class FeatureMappingScenarioView(LoggingMixin, generics.ListCreateAPIView):
    queryset = TestScenario.objects.all()
    serializer_class = TestScenarioSerializer
    filterset_fields = ['name']


class FeatureMappingScenarioDetailsView(LoggingMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = TestScenario.objects.all()
    serializer_class = TestScenarioSerializer
    filterset_fields = ['name']


class FeatureMappingScenarioTableView(LoggingMixin, generics.ListCreateAPIView):
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
        errors.append({'workbook format error': 'There must be 3 columns with "milestone", "feature" and "scenario"'
                                                ' data (column headers do not matter)'})
        errors.append({'workbook error': 'No rows found'})
        return errors

    first_row = next(rows)
    headings = [c.value for c in first_row]
    if len(headings) != 3:
        errors.append(
            {'workbook format error': 'There must be 3 columns with "milestone", "feature" and "scenario" data'
                                      ' (names do not matter)'})
        return errors

    fm_rules = []
    try:
        with transaction.atomic():
            mapping = FeatureMapping.objects.create(name=data['name'], owner_id=data['owner'],
                                                    component_id=data['component'], platform_id=data['platform'],
                                                    os_id=data['os'])

            for i, row in enumerate(rows):
                milestone_name, feature_name, scenario_name = [cell.value for cell in row]
                if all([milestone_name, feature_name, scenario_name]):
                    milestone, _ = Milestone.objects.get_or_create(name=milestone_name)
                    feature, _ = Feature.objects.get_or_create(name=feature_name)
                    scenario, _ = TestScenario.objects.get_or_create(name=scenario_name)

                    fm_rules.append(FeatureMappingRule(
                        mapping=mapping, milestone=milestone, feature=feature, scenario=scenario
                    ))
                else:
                    errors.append({f'workbook error (row {i + 2})': 'Empty cell'})
            FeatureMappingRule.objects.bulk_create(fm_rules)
    except IntegrityError as e:
        errors.append({'import error': f'Integrity error: {e.__cause__}'})

    return errors
