import json
import re
import copy
import urllib.parse
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional
from datetime import datetime
from urllib.parse import urlparse, urlunparse

import pandas as pd
import numpy as np
import dateutil.parser

from django.db import transaction
from django.db.models import Case, When, Q
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache
from django_filters.rest_framework import DjangoFilterBackend


from rest_framework import generics, status, filters
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse

import anytree.search
from anytree import Node
from anytree.exporter import JsonExporter

from sqlalchemy import and_
from sqlalchemy.orm import query, Query
from sqlalchemy.sql import func


from openpyxl.writer.excel import save_virtual_workbook

from . import excel
from api.models import Generation, Platform, Env, Component, Item, Driver, Status, Os, OsGroup, Validation, Action, \
    Result, ResultGroupNew, Run, FeatureMappingRule, ScenarioAsset, LucasAsset, MsdkAsset, FulsimAsset, Simics, FeatureMapping, \
    Feature
from api.serializers import UserSerializer, GenerationSerializer, PlatformSerializer, ComponentSerializer, \
    EnvSerializer, OsSerializer, ResultFullSerializer, ScenarioAssetSerializer, \
    ResultCutSerializer, LucasAssetSerializer, MsdkAssetSerializer, FulsimAssetSerializer, ScenarioAssetFullSerializer, \
    SimicsSerializer, LucasAssetFullSerializer, MsdkAssetFullSerializer, FulsimAssetFullSerializer, \
    DriverFullSerializer, StatusFullSerializer, FeatureMappingSerializer
from test_verifier.models import Codec
from test_verifier.serializers import CodecSerializer

from utils.api_logging import get_user_object, LoggingMixin
from utils.api_helpers import get_datatable_json, DefaultNameOrdering, CreateWOutputApiView, asset_view, \
    UpdateWOutputAPIView


@never_cache
def index(request):
    return render(request, 'api/index.html', {})


@never_cache
def test(request):
    return render(request, 'api/test.html', {})


# all requests that should managed by vue just pass to index
class PassToVue(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'api/index.html', {})


# Users block
class UserList(LoggingMixin, generics.ListAPIView):
    """ List Users """
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    filterset_fields = ['is_staff', 'username']


class CurrentUser(LoggingMixin, APIView):
    """ User's details """
    def get(self, request):
        user_object = get_user_object(request)
        user_data = UserSerializer(user_object).data
        return Response(user_data)


# Common data block

# Platform
class PlatformView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ List Platform objects """
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    filterset_fields = ['name', 'short_name', 'generation__name']


class PlatformTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ Platform table view formatted for DataTable """
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    filterset_fields = ['name', 'short_name', 'generation__name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False, exclude=['planning', 'weight'])


# Generation
class GenerationView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ List Generation objects """
    queryset = Generation.objects.all()
    serializer_class = GenerationSerializer
    filterset_fields = ['name']


class GenerationTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ Generation table view formatted for DataTable """
    queryset = Generation.objects.all()
    serializer_class = GenerationSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False)


# Os
class OsView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ List Os objects """
    queryset = Os.objects.all().prefetch_related('group')
    serializer_class = OsSerializer
    filterset_fields = {
        'name': ['exact'],
        'group__name': ['exact'],
        'weight': ['exact', 'gte', 'lte']
    }


class OsTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ Os table view formatted for DataTable """
    queryset = Os.objects.all()
    serializer_class = OsSerializer
    filterset_fields = {
        'name': ['exact'],
        'group__name': ['exact'],
        'weight': ['exact', 'gte', 'lte']
    }

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False, exclude=['group', 'weight'])


# Component
class ComponentView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ List Component objects """
    queryset = Component.objects.all()
    serializer_class = ComponentSerializer
    filterset_fields = ['name']


class ComponentTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ Component table view formatted for DataTable """
    queryset = Component.objects.all()
    serializer_class = ComponentSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False)


# Environment
class EnvView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ List Env objects """
    queryset = Env.objects.all()
    serializer_class = EnvSerializer
    filterset_fields = ['name']


class EnvTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ Env table view formatted for DataTable """
    queryset = Env.objects.all()
    serializer_class = EnvSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False)


class CodecView(LoggingMixin, DefaultNameOrdering, generics.ListCreateAPIView):
    """
        get: List Codec objects
        post: Create Codec object
    """
    queryset = Codec.objects.all()
    serializer_class = CodecSerializer
    filterset_fields = ['name']


class CodecDetailsView(LoggingMixin, generics.RetrieveUpdateDestroyAPIView):
    """ Codec single object management """
    queryset = Codec.objects.all()
    serializer_class = CodecSerializer
    filterset_fields = ['name']


class CodecTableView(LoggingMixin, DefaultNameOrdering, generics.ListAPIView):
    """ Codec table view formatted for DataTable """
    queryset = Codec.objects.all()
    serializer_class = CodecSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self)


class ResultView(LoggingMixin, generics.RetrieveAPIView):
    """ List of Result objects """
    queryset = Result.objects.all()
    serializer_class = ResultFullSerializer
    filterset_fields = ['validation_id', 'item_id']


class StatusView(LoggingMixin, generics.ListAPIView):
    """ List of Status objects """
    queryset = Status.objects.all()
    serializer_class = StatusFullSerializer
    filterset_fields = ['test_status']


class DriverView(LoggingMixin, DefaultNameOrdering, generics.ListCreateAPIView):
    """
        get: List Driver objects
        post: Create Driver object
    """
    queryset = Driver.objects.all()
    serializer_class = DriverFullSerializer
    filterset_fields = ['name']


class AbstractAssetView(LoggingMixin, generics.ListAPIView, CreateWOutputApiView):
    serializer_output_class = None
    serializer_class = None

    def post(self, request, *args, **kwargs):
        url = request.data['url']
        url_components = url.split('/')
        if len(url_components) == 1:
            # asset name is provided
            data = data = {'root': '', 'path': '', 'name': url_components[0], 'version': ''}
        else:
            # full url is provided
            parsed_url = urlparse(url)
            path = parsed_url.path if not parsed_url.path.startswith('/') else parsed_url.path[1:]
            path_components = path.split('/')
            if not parsed_url.scheme or not parsed_url.netloc or not path_components[0]:
                raise ParseError("Cannot parse url scheme or server")
            if len(path_components) < 3:
                raise ParseError("The path should contains '/artifactory/', asset name and version")
            root = urlunparse((parsed_url.scheme, parsed_url.netloc, path_components[0], '', '', ''))
            name, version = path_components[-2:]
            pure_path = '/'.join(path_components[1:-2])
            data = {'root': root, 'path': pure_path, 'name': name, 'version': version}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return self.serializer_output_class
        return self.serializer_class


# generate template views for Assets
# get: list of asset objects
# post: create asset object
ScenarioAssetView = asset_view(ScenarioAsset, ScenarioAssetFullSerializer, ScenarioAssetSerializer)
LucasAssetView = asset_view(LucasAsset, LucasAssetFullSerializer, LucasAssetSerializer)
MsdkAssetView = asset_view(MsdkAsset, MsdkAssetFullSerializer, MsdkAssetSerializer)
FulsimAssetView = asset_view(FulsimAsset, FulsimAssetFullSerializer, FulsimAssetSerializer)


class SimicsView(LoggingMixin, generics.ListCreateAPIView):
    """ List of Simics objects """
    queryset = Simics.objects.all()
    serializer_class = SimicsSerializer


class ResultUpdateView(LoggingMixin, generics.DestroyAPIView, UpdateWOutputAPIView):
    """
    put: Update existing Result object or replace it with new fields
    patch: Update only existing Result's fields
    delete: Delete Result by id
    """
    queryset = Result.objects.all()
    serializer_class = ResultCutSerializer
    serializer_output_class = ResultFullSerializer


def convert_to_datatable_json(dataframe: pd.DataFrame):
    d = json.loads(dataframe.to_json(orient='table'))

    headers = []
    for i, field in enumerate(d['schema']['fields']):
        text = str(field['name'])
        value = text.lower().replace(' ', '_')
        headers.append({'text': text, 'value': value})

    items = []
    for d_dict in d['data']:
        i_dict = {}
        for h_map in headers:
            i_dict[h_map['value']] = d_dict[h_map['text']]
        items.append(i_dict)

    return {'headers': headers, 'items': items}


def create_json_for_datatables(
    statuses: pd.DataFrame,
    result_ids: pd.DataFrame,
    id_to_name: Dict[int, str],
    total: int
    ):
    reverse_map = {v: k for k, v in id_to_name.items()}

    d = json.loads(statuses.to_json(orient='table'))
    headers = []
    for i, field in enumerate(d['schema']['fields']):
        text = str(field['name'])
        value = f'f{i}'
        headers.append({'text': text, 'value': value})

    result_ids = json.loads(result_ids.to_json(orient='table'))

    items = []
    for statuses, results in zip(d['data'], result_ids['data']):
        item = {}
        for header in headers:
            # value is something like f<N>
            # text is real header title
            key, value = header['value'], header['text']
            # handle pre-defined columns
            if value in ('Item name', 'Test ID', 'Codec', 'Feature'):
                item[key] = statuses[value]
            else:
                # validation columns
                status_dict = {'valId': reverse_map[value]}
                status = statuses[value]
                if status != '':
                    status_dict['status'] = status
                    result_id = results.get(value)
                    if result_id is not None:
                        if result_id != 0:
                            status_dict['tiId'] = result_id
                            del status_dict['valId']
                item[key] = status_dict

        items.append(item)

    return {'headers': headers, 'items': items, 'total': total}


ICONS = [
    'mdi-expansion-card',                                               # gen
    'mdi-chip',                                                         # platform
    (('windows', 'mdi-microsoft-windows'), ('linux', 'mdi-linux')),     # os group
    (('windows', 'mdi-microsoft-windows'), ('linux', 'mdi-linux')),     # os
    'mdi-memory',                                                       # env
    'mdi-format-list-bulleted-type'                                     # validation
]


class ValidationsView(LoggingMixin, APIView):
    def get(self, request, *args, **kwargs):
        filters_data = request.GET.get('data', {})
        if filters_data:
            filters_data = json.loads(filters_data)
            for f in filters_data:
                if all(key in f for key in ['start', 'end']):
                    f['start'] = dateutil.parser.isoparse(f['start'])
                    f['end'] = dateutil.parser.isoparse(f['end'])

        tree = Node('')

        validations_qs = Validation.objects.all().select_related('os__group', 'platform__generation', 'env')
        for validation in validations_qs.order_by('-platform__generation__weight', 'platform__weight',
                                                  'os__group__name',
                                                  'os__name', 'env__name', 'name'):
            # shortcuts
            platform = validation.platform
            os = validation.os

            # tree branch data: gen -> platform -> os.group -> os -> env -> validation name
            branch = (
                {'obj': platform.generation, 'name': platform.generation.name, 'level': 0},
                {'obj': platform, 'name': platform.short_name, 'level': 1},
                {'obj': os.group, 'name': os.group.name, 'level': 2},
                {'obj': os.group, 'name': os.name, 'level': 3},
                {'obj': validation.env, 'name': validation.env.name, 'level': 4},
                {'obj': validation, 'name': validation.name, 'level': 5}
            )

            # filter by input data
            if filters_data:
                ok = []
                for f in filters_data:
                    # date range check
                    if all(key in f for key in ['start', 'end']):
                        ok.append(f['start'] <= validation.date <= f['end'])

                    # tree levels check
                    else:
                        for node in branch:
                            if node['level'] == f['level']:
                                # validation name pattern check
                                if f['level'] == 5:
                                    if f['text'].lower() in node['name'].lower():
                                        ok.append(True)
                                        break
                                else:
                                    if node['name'] in f['text']:
                                        ok.append(True)
                                        break
                        else:
                            ok.append(False)

                if not all(ok):
                    continue

            parent = tree
            for node_data, icon_map in zip(branch, ICONS):
                # set icon according to tree level ICONS mapping
                icon, name = '', ''
                if isinstance(icon_map, tuple):
                    for alias in icon_map:
                        if node_data['obj'].name.lower() == alias[0]:
                            icon = alias[1]
                else:
                    icon = icon_map
                name = node_data['name']

                # find node by name and level, if not create new one
                node = anytree.search.find(parent, lambda n: n.name == name and n.level == node_data['level'])
                if not node:
                    node = Node(
                        parent=parent, name=name, text=name, text_flat=name,
                        selected=False, opened=True,
                        level=node_data['level'], id=node_data['obj'].id, klass=type(node_data['obj']).__name__,
                        icon=f'{icon} mdi tree-icon'
                    )
                parent = node

        exporter = JsonExporter()
        d = exporter.export(tree)

        # cut off root level to have Generation as first one on frontend
        d = json.loads(d).get('children', [])
        return Response(d)


class ValidationsDeleteByIdView(LoggingMixin, generics.DestroyAPIView):
    queryset = Validation.objects.all()

    @transaction.atomic
    def perform_destroy(self, instance):
        # get list of runs for this validation
        run_ids = list(Result.objects.filter(validation=instance).values_list('run', flat=True).distinct())

        # delete Validation object and linked Result objects due to cascade on_delete
        instance.delete()

        # detect unattended runs and delete them
        for run_id in run_ids:
            if Result.objects.filter(run_id=run_id).count() == 0:
                Run.objects.get(pk=run_id).delete()


class ValidationsFlatView(LoggingMixin, APIView):
    def get(self, request, *args, **kwargs):
        d = []
        ids = request.GET.get('ids', '')
        if ids:
            id_list = ids.split(',')
            validations_qs = Validation.objects.filter(id__in=id_list).order_by('-id')
        else:
            validations_qs = Validation.objects.all().order_by('-id')
        for v in validations_qs:
            d.append({
                'name': f'{v.name} ({v.platform.name}, {v.env.name}, {v.os.name})',
                'id': v.id
            })
        return Response(d)


def get_mappings_by_validations(serializer_class, validations, user):
    """ Filter mappings according to validation's platform, os and component from validation results """
    data = []
    components = Result.objects.filter(validation__in=validations).values_list('component', flat=True).distinct()
    for validation in validations:
        mappings = FeatureMapping.objects.filter(
            Q(component__in=components, platform=validation.platform, os=validation.os.group),
            Q(public=True) | Q(owner=user)
        )
        serializer = serializer_class(data=mappings, many=True)
        serializer.is_valid()

        for serialized_data in serializer.data:
            if serialized_data not in data:
                data.append(serialized_data)
    return data


class ValidationMappings(LoggingMixin, generics.GenericAPIView):
    serializer_class = FeatureMappingSerializer

    def get_queryset(self):
        ids = self.request.query_params.get('ids', None)
        if ids is not None:
            ids = [int(x) for x in ids.split(',')]
            return Validation.objects.filter(pk__in=ids)
        else:
            return Validation.objects.all()

    def get(self, request, *args, **kwargs):
        validations = self.get_queryset()
        return Response(
            get_mappings_by_validations(self.serializer_class, validations, get_user_object(request))
        )


class ValidationsStructureView(LoggingMixin, APIView):
    def get(self, request, *args, **kwargs):
        d = [
            {'name': 'gen', 'label': 'Generation', 'items': [], 'level': 0},
            {'name': 'platform', 'label': 'Platform', 'items': [], 'level': 1},
            {'name': 'os_group', 'label': 'OS Family', 'items': [], 'level': 2},
            {'name': 'os', 'label': 'OS', 'items': [], 'level': 3},
            # {'name': 'env', 'label': 'Env', 'items': [], 'level': 4},
        ]

        d[0]['items'] = Validation.objects.all().values_list('platform__generation__name', flat=True) \
            .order_by('-platform__generation__weight').distinct()
        d[1]['items'] = Validation.objects.all().values_list('platform__short_name', flat=True) \
            .order_by('-platform__weight').distinct()
        d[2]['items'] = Validation.objects.all().values_list('os__group__name', flat=True) \
            .order_by('os__group__name').distinct()
        d[3]['items'] = Validation.objects.all().values_list('os__name', flat=True) \
            .order_by('os__name').distinct()
        return Response(d)


class ReportBestView(LoggingMixin, APIView):
    def get(self, request: HttpRequest, val_pks: List[int], fmt_pks: Optional[List[int]] = None, *args, **kwargs) -> Response:
        if fmt_pks is None:
            fmt_pks = []
        do_excel = False
        if 'report' in request.GET and request.GET['report'] == 'excel':
            do_excel = True
        grouping = request.GET.get('group-by', 'feature')
        validations = Validation.objects.filter(pk__in=val_pks)

        # Looking for best items in target validations
        ibest = Result.sa \
            .query(Result.sa.item_id, func.max(Status.sa.priority).label('best_status_priority')) \
            .filter(Result.sa.validation_id.in_(val_pks),) \
            .join(Status.sa) \
            .group_by(Result.sa.item_id).subquery('ibest')

        # looking for date of best validation
        best = Result.sa.query(ibest.c.item_id, func.max(Status.sa.id).label('best_status'),
                               func.max(Validation.sa.date).label('best_validation_date')) \
            .select_from(Result.sa) \
            .join(Status.sa, Status.sa.id == Result.sa.status_id)\
            .join(Validation.sa, Validation.sa.id == Result.sa.validation_id) \
            .join(ibest, Result.sa.item_id == ibest.c.item_id) \
            .filter(Result.sa.validation_id.in_(val_pks), Status.sa.priority == ibest.c.best_status_priority) \
            .group_by(ibest.c.item_id).subquery('best')

        v2 = Result.sa.query(Result.sa.item_id, Validation.sa.id, Result.sa.status_id, Validation.sa.date) \
            .filter(Result.sa.validation_id.in_(val_pks),) \
            .join(Validation.sa) \
            .subquery('v2')

        # Looking for best validation in found date
        vbest = Result.sa.query(best.c.item_id, func.max(v2.c.id).label('best_validation'),
                                func.max(best.c.best_status).label('best_status_id')) \
            .select_from(best) \
            .join(v2, and_(v2.c.item_id == best.c.item_id, v2.c.status_id == best.c.best_status,
                           v2.c.date == best.c.best_validation_date)) \
            .group_by(best.c.item_id) \
            .subquery('vbest')

        # Looking for best results in found validations
        res = Result.sa.query(vbest.c.item_id, vbest.c.best_validation, vbest.c.best_status_id,
                              func.max(Result.sa.id).label('result')) \
            .select_from(vbest) \
            .join(Result.sa,
                  and_(Result.sa.item_id == vbest.c.item_id, Result.sa.validation_id == vbest.c.best_validation,
                       Result.sa.status_id == vbest.c.best_status_id)) \
            .group_by(vbest.c.item_id, vbest.c.best_validation, vbest.c.best_status_id)

        # Select scenario ids, feature names, codec names from feature mapping rules which belong to selected FMTs
        fm_rules = fmt_rules(fmt_pks).subquery('fm_rules')

        # joining referenced tables to get names and so on
        res = res.subquery('res')
        q = Result.sa.query(
            (fm_rules.c.Feature if grouping == 'feature' else fm_rules.c.Codec).label('group'),
            Item.sa.name.label('item_name'), fm_rules.c.Codec,
            res.c.best_status_id, Validation.sa.name.label('val_name'), Driver.sa.name.label('driver_name'),
            Result.sa.item_id, Result.sa.validation_id, Validation.sa.source_file, Result.sa.result_url) \
            .select_from(res) \
            .join(Item.sa, Item.sa.id == res.c.item_id) \
            .join(Result.sa, Result.sa.id == res.c.result) \
            .join(fm_rules, Item.sa.scenario_id == fm_rules.c.scenario_id, full=True) \
            .join(Validation.sa) \
            .join(Driver.sa) \
            .order_by(fm_rules.c.Feature if grouping == 'feature' else fm_rules.c.Codec, Item.sa.name)

        # Create DataFrame crosstab from SQL request
        df = pd.read_sql(q.statement, q.session.bind)
        df['group'] = df['group'].fillna('Unknown')
        if grouping == 'feature' and fmt_pks:
            # extend feature name with codec
            df = df.apply(lambda row: feature_codec_concat(row), axis=1)
        df.drop('Codec', axis=1)

        if df.empty:
            if do_excel:
                return Response()
            return Response({'headers': [], 'items': []})

        ct = pd.crosstab(index=df.group,
                         values=df.item_name, columns=df.best_status_id, aggfunc='count',
                         colnames=[''],
                         margins=True, margins_name='Total', dropna=False)

        # prepare DataFrame crosstab for response
        ct = prepare_crosstab(ct, grouping)
        # If no excel report needed just finish here with json return
        if not do_excel:
            return Response(convert_to_datatable_json(ct))

        # Excel part
        workbook = excel.do_report(data=ct, extra=validations, report_name='Best status report')

        filename = f'best_report_{datetime.now():%Y-%m-%d_%H:%M:%S}.xlsx'
        response = HttpResponse(save_virtual_workbook(workbook), content_type="application/ms-excel")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ReportLastView(LoggingMixin, APIView):
    def get(self, request: HttpRequest, val_pks: List[int], fmt_pks: Optional[List[int]] = None, *args, **kwargs) -> Response:
        if fmt_pks is None:
            fmt_pks = []
        do_excel = False
        if 'report' in request.GET and request.GET['report'] == 'excel':
            do_excel = True
        grouping = request.GET.get('group-by', 'feature')
        validations = Validation.objects.filter(pk__in=val_pks)
        # Looking for last items in target validations with best status priority
        ilast = Result.sa \
            .query(Result.sa.item_id, func.max(Validation.sa.date).label('last_validation_date'),
                   func.max(Status.sa.priority).label('best_status_priority')) \
            .select_from(Result.sa) \
            .join(Validation.sa, Validation.sa.id == Result.sa.validation_id) \
            .join(Status.sa, Status.sa.id == Result.sa.status_id) \
            .filter(Validation.sa.id.in_(val_pks), ) \
            .group_by(Result.sa.item_id).subquery('ibest')

        # Select last validation ids (last == max id) for items with best status priority
        vBest = Result.sa \
            .query(ilast.c.item_id, func.max(Result.sa.validation_id).label('last_validation_id'),
                   ilast.c.best_status_priority) \
            .select_from(Result.sa) \
            .join(ilast, Result.sa.item_id == ilast.c.item_id) \
            .join(Validation.sa, Validation.sa.id == Result.sa.validation_id) \
            .filter(Validation.sa.id.in_(val_pks), Validation.sa.date == ilast.c.last_validation_date) \
            .group_by(ilast.c.item_id, ilast.c.best_status_priority).subquery('vbest')

        # Select last status ids and last result ids for items from last validations with best status priority
        res = Result.sa \
            .query(vBest.c.item_id, vBest.c.last_validation_id, func.max(Result.sa.status_id).label('last_status_id'),
                   func.max(Result.sa.id).label('result_id'), vBest.c.best_status_priority) \
            .select_from(vBest) \
            .join(Result.sa,
                  and_(Result.sa.item_id == vBest.c.item_id, Result.sa.validation_id == vBest.c.last_validation_id)) \
            .filter(Result.sa.id.isnot(None)) \
            .group_by(vBest.c.item_id, vBest.c.last_validation_id, vBest.c.best_status_priority)

        # Select scenario ids, feature names, codec names from feature mapping rules which belong to selected FMTs
        fm_rules = fmt_rules(fmt_pks).subquery('fm_rules')

        # joining referenced tables to get names and so on
        res = res.subquery('res')
        final_query = Result.sa.query(
            (fm_rules.c.Feature if grouping == 'feature' else fm_rules.c.Codec).label('group'),
            Item.sa.name.label('item_name'), fm_rules.c.Codec,
            res.c.last_status_id, Validation.sa.name.label('val_name'), Driver.sa.name.label('driver_name'),
            Result.sa.item_id, Result.sa.validation_id, Validation.sa.source_file, Result.sa.result_url) \
            .select_from(res) \
            .join(Item.sa, Item.sa.id == res.c.item_id) \
            .join(Result.sa, Result.sa.id == res.c.result_id) \
            .join(fm_rules, Item.sa.scenario_id == fm_rules.c.scenario_id, full=True) \
            .join(Validation.sa) \
            .join(Driver.sa) \
            .order_by(fm_rules.c.Feature if grouping == 'feature' else fm_rules.c.Codec, Item.sa.name)

        df = pd.read_sql(final_query.statement, final_query.session.bind)
        df['group'] = df['group'].fillna('Unknown')
        if grouping == 'feature' and fmt_pks:
            # extend feature name with codec
            df = df.apply(lambda row: feature_codec_concat(row), axis=1)
        df.drop('Codec', axis=1)

        # Create DataFrame crosstab from SQL request
        if df.empty:
            if do_excel:
                return Response()
            return Response({'headers': [], 'items': []})

        ct = pd.crosstab(index=df.group,
                         values=df.item_name, columns=df.last_status_id, aggfunc='count',
                         colnames=[''],
                         margins=True, margins_name='Total', dropna=False)
        # prepare DataFrame crosstab for response
        ct = prepare_crosstab(ct, grouping)
        # If no excel report needed just finish here with json return
        if not do_excel:
            return Response(convert_to_datatable_json(ct))

        # Excel part
        workbook = excel.do_report(data=ct, extra=validations, report_name='Last status report')

        filename = f'last_report_{datetime.now():%Y-%m-%d_%H:%M:%S}.xlsx'
        response = HttpResponse(save_virtual_workbook(workbook), content_type="application/ms-excel")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


def prepare_crosstab(ct: pd.DataFrame, grouping: str):
    all_status_ids = list(Status.objects.all().order_by('priority').values_list('id', flat=True))
    status_mapping = dict(Status.objects.all().values_list('id', 'test_status'))

    # reindex columns by priority and adding notrun and passrate empty ones
    ct = ct.reindex(columns=all_status_ids + ['Total', 'Not run', 'Passrate'])
    ct.rename(columns=status_mapping, inplace=True)
    ct.index.names = ['Feature'] if grouping == 'feature' else ['Codec']  # rename group_name index name

    # Not run column
    notrun = (ct['Blocked'].fillna(0) + ct['Skipped'].fillna(0) + ct['Canceled'].fillna(0)).round(3).astype(int)
    ct['Not run'] = notrun

    # Passrate column
    passrate = 100 * ct['Passed'].fillna(0) / (ct['Total'] - ct['Not run'])
    ct['Passrate'] = passrate.round(2).astype(str) + '%'

    # leave only needed columns
    ct = ct[['Not run', 'Error', 'Failed', 'Passed', 'Total', 'Passrate']]
    ct = ct.replace(np.nan, '', regex=False).replace(0, '', regex=False)
    return ct


def feature_codec_concat(row: pd.Series):
    if row['Codec']:
        # replace all spaces in codec with non-breaking spaces
        codec = row['Codec'].replace(' ', '\u00A0')
        row['group'] = f"{row['group']} - {codec}"
    return row


def fmt_rules(fmt_pks: Optional[List[int]] = None) -> Query:
    return FeatureMappingRule.sa \
        .query(FeatureMappingRule.sa.scenario_id, Feature.sa.name.label('Feature'),
               Codec.sa.name.label('Codec')) \
        .select_from(FeatureMappingRule.sa) \
        .filter(FeatureMappingRule.sa.mapping_id.in_(fmt_pks)) \
        .join(FeatureMapping.sa) \
        .join(Feature.sa) \
        .join(Codec.sa)


def validation_id_to_name(validation_ids: List[int]) -> Dict[int, str]:
    result = {}
    for v in Validation.objects.filter(id__in=validation_ids):
        result[int(v.id)] = f'{v.name}\n({v.platform.short_name}, {v.env.name}, {v.os.name})'
    return result


def generate_dataframe(sql: Query, value: str) -> pd.DataFrame:
    df = pd.read_sql(sql.statement, sql.session.bind)
    ct = pd.crosstab(index=df.item_id, columns=df.validation_id, values=df[value], aggfunc='max')
    ct = pd.merge(ct, df, on='item_id', how='outer', right_index=True)
    ct.index.names = ['Item ID']

    del ct[value]
    del ct['status_id']
    del ct['validation_id']
    ct = ct.drop_duplicates()
    del ct['id']

    return ct


def get_result_ids(validation_ids: List[int]) -> pd.DataFrame:
    q = Result.sa \
        .query(func.max(Result.sa.status_id).label('status_id'), Result.sa.id.label('result_id'),
               Result.sa.item_id, Item.sa.id, Validation.sa.id.label('validation_id')) \
        .select_from(Result.sa) \
        .filter(Result.sa.validation_id.in_(validation_ids)) \
        .join(Item.sa).join(Validation.sa) \
        .group_by(Result.sa.id, Result.sa.item_id, Item.sa.id, Validation.sa.id)

    ct = generate_dataframe(q, 'result_id')
    ct = ct.replace(np.nan, 0, regex=False)

    types = {col: 'int32' for col in validation_ids if col in ct}
    ct = ct.astype(types)
    # renaming columns
    id_to_name = validation_id_to_name(validation_ids)
    ct.rename(columns=id_to_name, inplace=True)

    return ct


def update_feature_and_codec(row: pd.Series, df: pd.DataFrame) -> None:
    feature_and_codec =  df.loc[df['scenario_id'] == row.scenario_id]
    if not feature_and_codec.empty:
        # to prevent strange effect with list of single
        # element inside...
        row['Feature'] = feature_and_codec['Feature'].values[0]
        row['Codec'] = feature_and_codec['Codec'].values[0]

    return row


def replace_item_id(row: pd.Series, items_dict: Dict[int, str]) -> pd.Series:
    row["Item name"] = items_dict[row["Item name"]]
    return row


def validation_statuses(validation_ids: List[int], fmt_pks: List[int]) -> pd.DataFrame:
    q = Result.sa \
        .query(func.max(Result.sa.status_id).label('status_id'), Item.sa.test_id, Item.sa.scenario_id,
               Result.sa.item_id, Item.sa.id, Validation.sa.id.label('validation_id')) \
        .select_from(Result.sa) \
        .filter(Result.sa.validation_id.in_(validation_ids)) \
        .join(Item.sa).join(Validation.sa) \
        .group_by(Item.sa.test_id, Result.sa.item_id, Item.sa.id, Validation.sa.id)

    df = pd.read_sql(q.statement, q.session.bind)
    ct = pd.crosstab(index=df.item_id, columns=df.validation_id, values=df.status_id, aggfunc='max')
    ct = pd.merge(ct, df, on='item_id', how='outer', right_index=True)
    ct.index.names = ['Item name']  # rename group_name index name
    del ct['status_id']
    del ct['validation_id']
    ct = ct.drop_duplicates()
    del ct['id']

    q = fmt_rules(fmt_pks)

    df = pd.read_sql(q.statement, q.session.bind)
    ct['Codec'] = 'n/a'
    ct['Feature'] = 'n/a'
    # could be very non-optimal solution for big validations...
    ct = ct.apply(lambda x: update_feature_and_codec(x, df), axis=1)
    del ct['scenario_id']

    # replace status_id with test_status values
    status_mapping = dict(Status.objects.all().values_list('id', 'test_status'))
    for v_id in validation_ids:
        # check if validaton_id column is in DataFrame, i.e. we have items to show for this id
        if v_id in ct:
            ct[v_id] = ct[v_id].map(status_mapping)

    # replace NaNs which appeared as result of all previous actions with empty strings
    ct = ct.replace(np.nan, '', regex=False)

    # move Item name, Feature, and Codec columns to front
    cols = ct.columns.tolist()
    cols = cols[-3:] + list(map(lambda x: int(x), validation_ids))
    ct = ct.reindex(columns=cols)

    ct.rename(columns={'test_id': 'Test ID'}, inplace=True)

    return ct


class ReportCompareView(LoggingMixin, APIView):
    def get(self, request: HttpRequest, val_pks: List[int], fmt_pks: Optional[List[int]] = None, *args, **kwargs) -> Response:
        if fmt_pks is None:
            fmt_pks = []

        do_excel = False
        if 'report' in request.GET and request.GET['report'] == 'excel':
            do_excel = True

        show = request.GET.get('show', 'all,show_passed').split(',')
        if len(show) == 2:
            show_diff, hide_passed = show

        show_diff = (show_diff == 'diff')
        hide_passed = (hide_passed == 'hide_passed')

        statuses = validation_statuses(val_pks, fmt_pks)
        result_ids = get_result_ids(val_pks)

        total = len(statuses)
        if show_diff:
            # drop rows where all statuses are equal
            mask = statuses.apply(lambda row: len(row.loc[val_pks].unique()) > 1, axis=1)
            statuses = statuses[mask]
            result_ids = result_ids[mask]
        elif hide_passed:
            # drop rows with only passed statuses
            mask = statuses.apply(lambda row: (len(row.loc[val_pks].unique()) > 1 or 'Passed' not in row.loc[val_pks].unique()), axis=1)
            statuses = statuses[mask]
            result_ids = result_ids[mask]

        id_to_name = validation_id_to_name(val_pks)
        statuses.rename(columns=id_to_name, inplace=True)

        items_dict = dict(
            Result.objects
                .filter(validation_id__in=val_pks)
                .values_list('item_id', 'item__name')
        )
        statuses.reset_index(inplace=True)
        statuses = statuses.apply(lambda row: replace_item_id(row, items_dict), axis=1)
        statuses.set_index("Item name", inplace=True)

        # If no excel report needed just finish here with json return
        if not do_excel:
            return Response(create_json_for_datatables(statuses, result_ids, id_to_name, total))

        # Excel part
        workbook = excel.do_comparison_report(statuses)

        filename = f'comparison_report_{datetime.now():%Y-%m-%d_%H:%M:%S}.xlsx'
        response = HttpResponse(save_virtual_workbook(workbook), content_type="application/ms-excel")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ExtraDataView(LoggingMixin, APIView):
    def get(self, request: HttpRequest, ti_pks: List[str], *args, **kwargs) -> Response:
        extra_data = []
        item_name = None
        for res_pk in ti_pks:
            datum = {}
            if res_pk.startswith('v'):
                val = get_object_or_404(Validation, pk=int(res_pk[1:]))
                datum['vinfo'] = {
                    'validation': val.name,
                    'platform': val.platform.short_name,
                    'os':  val.os.name,
                    'env':  val.env.name
                }
            else:
                res = get_object_or_404(Result, pk=int(res_pk))
                item_name = res.item.name
                val = res.validation
                datum['vinfo'] = {
                    'validation': val.name,
                    'platform': val.platform.short_name,
                    'os':  val.os.name,
                    'env':  val.env.name
                }
                datum['status'] = res.status.test_status
                additional_parameters = {
                    'avg_psnr': '',
                    'avg_ssim': '',
                    'extreme_psnr': '',
                    'extreme_ssim': '',
                    'file_size': '',
                    'error_features': ''
                }
                if res.additional_parameters:
                    additional_parameters.update(res.additional_parameters)
                datum['additional_parameters'] = additional_parameters

                datum['assets'] = {
                    'msdk': str(res.msdk_asset),
                    'lucas': str(res.lucas_asset),
                    'scenario': str(res.scenario_asset),
                    'fullsim': str(res.fulsim_asset),
                    'os': str(res.os_asset),
                }
            extra_data.append(datum)

        return Response({
            'item': item_name,
            'extra': extra_data
        })


@dataclass
class Part:
    os: str = ''
    env: str = ''
    platform: str = ''
    number: int = 2
    validation_ids: list = None


class ReportFromSearchView(LoggingMixin, APIView):
    def get(self, request, *args, **kwargs):
        # list of tuples (env_shortcut, full_env) - (sim, Simulation)
        env_names_shortnames = [(shortcut.lower(), name)
                                for shortcut, name in list(Env.objects.values_list('short_name', 'name'))]
        # add list of tuples - (full_env.lower(), full_env) - (simulation, Simulation), create mapping
        envs = dict(env_names_shortnames + [(name.lower(), name) for shortname, name in env_names_shortnames])

        # '19h1': 'Windows 10 19H1'
        oses = {shortcut: name for name, shortcut in Os.objects.values_list('name', 'shortcut') if shortcut}

        oses_groups = {alias: name
                       for name, aliases in OsGroup.objects.values_list('name', 'aliases')
                       for alias in aliases.split(',')}  # {'name': 'Linux', 'aliases': 'lin,linux,ubuntu'}

        platforms = {}
        platform_shortnames = list(Platform.objects.values_list('short_name', flat=True))
        for i, pl in enumerate(platform_shortnames):  # create platform mapping
            name_parts = pl.split('-')  # 'tgl-lp' -> ['tgl', 'lp']
            core_platform_name = name_parts[0]
            if len(name_parts) > 1:  # if have suffix: 'lp' in 'tgl-lp' for instance
                # search for another versions of platform: 'tgl', 'tgl-lp'
                for _pl in platform_shortnames:
                    if _pl != pl and _pl.startswith(core_platform_name):
                        break  # another version is found
                else:
                    pl = core_platform_name  # no another version found
            platforms[pl.lower()] = platform_shortnames[i]  # {'ats': 'ATS', 'tgl': 'TGL-LP'}
        # to return platform in recognized query {'ATS': 'ats', 'TGL-LP': 'tgl'}
        platform_reverse_map = {val: key.upper() for key, val in platforms.items()}

        query = request.GET['query'].lower().strip()
        if not query:
            response = 'empty query'
            return Response(data=response, status=status.HTTP_400_BAD_REQUEST)

        actions = list(Action.objects.values_list('name', flat=True))  # example: last, best, compare (reports)
        action = Action._meta.get_field('name').get_default()
        for act in actions:
            if act in query:
                action = act
                query = query.replace(action, '').strip()  # remove action from the query
        recognized_query = action

        # if have with statements -> will choose validations from different branches
        # parts of the query (branches): compare tgl lin with ats win sim
        query_parts = query.split('with')
        parts = [Part() for _ in query_parts]

        last_found_os = last_found_platform = ''
        validation_ids = []
        for query_part, part in zip(query_parts, parts):
            words = re.split(r'\s+', query_part)
            platform, found_platforms = self.extract_platform(words, platforms)
            if platform:
                last_found_platform = platform
            else:
                # in some cases we need to use platform from previous part of the query
                # example: 'compare tgl lin with win' - use tgl for both parts
                platform = last_found_platform
            env, found_envs = self.extract_env(words, envs)
            number_of_validations = 2 if len(parts) == 1 else 1
            number = self.extract_number(query_part, default_number=number_of_validations)
            os, found_oses = self.extract_os(words, env, platform, oses, oses_groups)
            if os:
                last_found_os = os

            duplicated_keywords = []
            for kw, found_values in zip(['os', 'environment', 'platform'], [found_oses, found_envs, found_platforms]):
                if len(found_values) > 1:
                    duplicated_keywords.append(f"{kw} - {', '.join(found_values)}")
            if duplicated_keywords:
                response = 'found duplicates: ' + ', '.join(duplicated_keywords)
                return Response(data=response, status=status.HTTP_400_BAD_REQUEST)
            for name, val in zip(['os', 'env', 'platform', 'number'], [os, env, platform, number]):
                setattr(part, name, val)

        # check on missing keywords
        missed = []
        if not last_found_os:
            missed.append('os')
        if not last_found_platform:
            missed.append('platform')
        if missed:
            # return hints
            hint = 'cannot find ' + ', '.join(missed)
            return Response(data=hint, status=status.HTTP_400_BAD_REQUEST)
        # recognized query for every part: '1 tgl ubuntu 18.04 silicon' for part 'tgl lin'
        recognized_parts = []
        # last os, platform are to use keywords from another parts
        # compare tgl lin with win - use tgl platform for the second part of the query
        for part in parts:
            # if os or platform is not found in this part -> use last found elements
            if part.os:
                last_found_os = part.os
            else:
                part.os = last_found_os
            if part.platform:
                last_found_platform = part.platform
            else:
                part.platform = last_found_platform
            recognized_parts.append(f" {part.number} {part.env.lower()} {part.os.lower()} "
                                    f"{platform_reverse_map[part.platform]}")
            part.validation_ids = \
                Validation.objects.filter(
                    env__name__in=[part.env], platform__short_name__in=[part.platform], os__name__in=[part.os]
                ).order_by('-date').values_list('id', flat=True)[:part.number]

            if not part.validation_ids:
                hint = f"no validations found for query: {part.env.lower()} " \
                       f"{platform_reverse_map[part.platform]} {part.os.lower()}"
                return Response(data=hint, status=status.HTTP_404_NOT_FOUND)
            validation_ids += part.validation_ids
        recognized_query += ' with'.join(recognized_parts)
        if not validation_ids:
            hint = 'no validations found for query: ' + recognized_query
            return Response(data=hint, status=status.HTTP_404_NOT_FOUND)

        original_order = Case(*[When(pk=pk, then=position) for position, pk in enumerate(validation_ids)])
        validation_data = Validation.objects.filter(pk__in=validation_ids) \
            .values_list(
                'platform__generation__name', 'platform__short_name', 'os__group__name', 'os__name', 'env__name', 'name'
            ).order_by(original_order)

        return Response({
            'action': action,
            'description': recognized_query,
            'validations_data': validation_data,
            'validations_ids': validation_ids
        })

    @staticmethod
    def extract_platform(words: List[str], platforms: Dict[str, str]) -> Tuple[str, List[str]]:
        platform = ''
        found_platforms = []
        for pl in platforms:
            if pl in words:
                platform = platforms[pl]
                found_platforms.append(pl.lower())
        return platform, found_platforms

    @staticmethod
    def extract_env(words: List[str], envs: Dict[str, str]) -> Tuple[str, List[str]]:
        environment = 'Silicon'
        found_envs = []
        for env in envs:
            if env in words:
                environment = envs[env]
                found_envs.append(env)
        return environment, found_envs

    @staticmethod
    def extract_number(query: str, default_number: int) -> int:
        number = default_number
        # search for the number of validations in the beginning of the query
        found_number = re.match(r'\s*\d+', query)
        if found_number:
            number = int(found_number.group(0))
        else:
            str_numbers = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
            pattern = '|'.join(str_numbers)  # pattern - any of the numbers in list str_numbers
            found_number = re.match(pattern, query)
            if found_number:
                number = str_numbers.index(found_number.group(0)) + 1
        return number

    @staticmethod
    def extract_os(words: List[str], env: str, platform: str,
                   oses: Dict[str, str], oses_groups: Dict[str, str]) -> Tuple[str, List[str]]:
        os = ''
        found_oses = []
        # try to find specific os (search for version of os, example: 18.04 or 19h1)
        for os_ in oses:
            if os_ in words:
                os = oses[os_]
                found_oses.append(os_.lower())
        # if os isn't found -> try to find os group: win/lin/ubuntu
        if not os and platform and env:
            os_group = ''
            for os_group_ in oses_groups:
                if os_group_ in words:
                    os = oses_groups[os_group_]
                    os_group = os_group_
                    found_oses.append(os_group_.lower())
            if os:  # os group is found in query
                os_group_id = Os.objects.filter(name__in=[os]).values_list('id', flat=True)
                existed_oses = Validation.objects \
                    .filter(env__name__in=[env], platform__short_name__in=[platform]) \
                    .values_list('os', flat=True).distinct()
                os = os_group
                if existed_oses:
                    group_oses = Os.objects.filter(group__in=os_group_id, id__in=existed_oses) \
                        .order_by('-weight') \
                        .values_list('name', flat=True)
                    if group_oses:
                        os = group_oses[0]  # the latest os
        return os, found_oses


class RequestModelCreation(APIView):
    def post(self, request):
        model = request.data['model']
        fields = request.data['fields']
        requester = request.data['requester']
        staff_emails = get_user_model().staff_emails()

        # field names and values to be inserted into the url and later will be inserted into the form on the admin page
        autocomplete_data = '?' + urllib.parse.urlencode(fields)

        if 'generation' in fields:
            # show gen name instead of id in email to admins
            fields['generation'] = Generation.objects.get(pk=fields['generation']).name
        # url to create new object on the admin page
        url = request.build_absolute_uri(reverse(f'admin:api_{model.lower()}_add')) + autocomplete_data
        msg = render_to_string('request_creation.html', {'first_name': requester['first_name'],
                                                         'last_name': requester['last_name'],
                                                         'username': requester['username'],
                                                         'email': requester['email'],
                                                         'model': model.lower(),
                                                         'fields': fields,
                                                         'add_model_object_url': url})
        subject = f'[REPORTER] New {model.lower()} creation request'
        sender = 'reporter@intel.com'

        msg = EmailMessage(subject, msg, sender, staff_emails, cc=[requester['email']])
        msg.content_subtype = "html"
        try:
            msg.send()
            return Response()
        except Exception:
            return Response(data='Failed to send email', status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportIndicatorView(APIView):
    def get(self, request, id, *args, **kwargs):
        def update_status(data, total, status):
            key_to_update = None
            if status == 'Passed':
                key_to_update = 'passed'
            elif status == 'Failed':
                key_to_update = 'failed'
            elif status in ('Skipped', 'Blocked', 'Canceled'):
                key_to_update = 'blocked'

            data[key_to_update] += 1
            data['executed'] += 1
            total[key_to_update] += 1
            total['executed'] += 1

        mapping_ids = request.GET.get('fmt_id').split(',')
        mode = request.GET.get('mode')
        do_excel = False
        if 'report' in request.GET and request.GET['report'] == 'excel':
            do_excel = True

        data = defaultdict(dict)
        total = {'executed': 0, 'passed': 0, 'failed': 0, 'blocked': 0}

        results = Result.objects.filter(validation_id=id)
        # get mappings with preserved ids order from request
        original_order = Case(*[When(pk=pk, then=position) for position, pk in enumerate(mapping_ids)])
        mappings = FeatureMapping.objects.filter(pk__in=mapping_ids).order_by(original_order)

        for mapping in mappings:
            mapping_data = defaultdict(dict)
            mapping_total = {'executed': 0, 'passed': 0, 'failed': 0, 'blocked': 0}

            for milestone, scenario_id, feature, ids in FeatureMappingRule.objects.filter(mapping_id=mapping.id) \
                    .values_list('milestone__name', 'scenario_id', 'feature__name', 'ids'):
                if mode == 'combined':
                    feature_name = f'{feature} ({mapping.codec.name})'
                else:
                    feature_name = feature

                mapping_data[milestone][feature_name] = {'executed': 0, 'passed': 0, 'failed': 0, 'blocked': 0}

                if ids is not None:
                    ids = ids.split(',')
                    for status in results.filter(item__scenario_id=scenario_id, item__test_id__in=ids) \
                            .values_list('status__test_status', flat=True):
                        update_status(mapping_data[milestone][feature_name], mapping_total, status)
                else:
                    for status in results.filter(item__scenario_id=scenario_id).values_list('status__test_status', flat=True):
                        update_status(mapping_data[milestone][feature_name], mapping_total, status)

            if mode == 'single' and do_excel:
                # split data by mappings
                data[mapping.id]['items'] = copy.deepcopy(mapping_data)
                data[mapping.id]['total'] = copy.deepcopy(mapping_total)
            else:
                # merge to one dict
                for key, value in mapping_data.items():
                    for subkey, subvalue in value.items():
                        data[key][subkey] = subvalue
                for key in ['passed', 'failed', 'blocked', 'executed']:
                    total[key] += mapping_total[key]

        if not data:
            if do_excel:
                return Response()
            return Response({'headers': [], 'items': []})

        if not do_excel:
            # Data-table formatting
            headers, items = [], []
            for label in ('milestone', 'feature', 'passed', 'failed', 'blocked', 'executed'):
                headers.append({
                    'text': label.capitalize(),
                    'value': label,
                    'groupable': True if label == 'milestone' else False,
                    'width': 150 if label not in ('milestone', 'feature') else None,
                })

            for milestone, m_data in data.items():
                for feature, f_data in m_data.items():
                    items.append({'milestone': milestone, 'feature': feature, **f_data})
            items.append(total)
            return Response({'headers': headers, 'items': items})
        else:
            # Excel part
            validation = Validation.objects.get(id=id)

            if mode == 'combined':
                excel_data = {'items': data, 'total': total}
            else:
                excel_data = data
            workbook = excel.do_indicator_report(excel_data, validation, mappings, mode)
            filename = f'indicator_report_{datetime.now():%Y-%m-%d_%H:%M:%S}.xlsx'
            response = HttpResponse(save_virtual_workbook(workbook), content_type="application/ms-excel")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response


class ResultHistoryView(LoggingMixin, APIView):
    def get(self, request, pk, *args, **kwargs):
        result = get_object_or_404(Result, pk=pk)
        history_records = list(result.history.all())
        if len(history_records) < 2:
            return Response([])
        old_record = history_records[-1]
        changes = []
        for new_record in history_records[-2::-1]:
            delta = new_record.diff_against(old_record)
            diff = {'user': new_record.history_user.username if new_record.history_user else None,
                    'date': new_record.history_date,
                    'reason': new_record.history_change_reason,
                    'changes': []}
            for change in delta.changes:
                field = change.field
                try:
                    old_value = str(getattr(delta.old_record, field))
                except Exception:
                    old_value = None
                try:
                    new_value = str(getattr(delta.new_record, field))
                except Exception:
                    new_value = None
                diff['changes'].append({'field': change.field, 'old': old_value, 'new': new_value})
            changes.insert(0, diff)
            old_record = new_record
        return Response(changes)