import json
import re
import urllib.parse
from dataclasses import dataclass
from typing import Dict, Tuple, List

import pandas as pd
import numpy as np
import dateutil.parser

from datetime import datetime

import django_filters.rest_framework
from django.core.mail import EmailMessage

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.reverse import reverse

from .serializers import *

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from anytree import Node, AnyNode
from anytree.search import find_by_attr
from anytree.exporter import JsonExporter

from sqlalchemy.sql import func
from sqlalchemy import and_

from openpyxl.writer.excel import save_virtual_workbook

from . import excel
from .models import *

from reporting.settings import production

from utils.api_logging import get_user_object, LoggingMixin
from utils.api_helpers import get_datatable_json


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
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    filterset_fields = ['is_staff', 'username']


class CurrentUser(LoggingMixin, APIView):
    def get(self, request):
        user_object = get_user_object(request)
        user_data = UserSerializer(user_object).data
        return Response(user_data)


# Common data block
# Platform
class PlatformView(LoggingMixin, generics.ListAPIView):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    filterset_fields = ['name', 'short_name', 'generation__name']


class PlatformTableView(LoggingMixin, generics.ListAPIView):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    filterset_fields = ['name', 'short_name', 'generation__name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False, exclude=['planning', 'weight'])


# Generation
class GenerationView(LoggingMixin, generics.ListAPIView):
    queryset = Generation.objects.all()
    serializer_class = GenerationSerializer
    filterset_fields = ['name']


class GenerationTableView(LoggingMixin, generics.ListAPIView):
    queryset = Generation.objects.all()
    serializer_class = GenerationSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False)


# Os
class OsView(LoggingMixin, generics.ListAPIView):
    queryset = Os.objects.all().prefetch_related('group')
    serializer_class = OsSerializer
    filterset_fields = {
        'name': ['exact'],
        'group__name': ['exact'],
        'weight': ['exact', 'gte', 'lte']
    }


class OsTableView(LoggingMixin, generics.ListAPIView):
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
class ComponentView(LoggingMixin, generics.ListAPIView):
    queryset = Component.objects.all()
    serializer_class = ComponentSerializer
    filterset_fields = ['name']


class ComponentTableView(LoggingMixin, generics.ListAPIView):
    queryset = Component.objects.all()
    serializer_class = ComponentSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False)


# Environment
class EnvView(LoggingMixin, generics.ListAPIView):
    queryset = Env.objects.all()
    serializer_class = EnvSerializer
    filterset_fields = ['name']


class EnvTableView(LoggingMixin, generics.ListAPIView):
    queryset = Env.objects.all()
    serializer_class = EnvSerializer
    filterset_fields = ['name']

    def get(self, request, *args, **kwargs):
        return get_datatable_json(self, actions=False)


ICONS = [
    'i-gen',
    'i-platform',
    (('windows', 'i-windows'), ('linux', 'i-linux')),
    (('windows', 'i-windows'), ('linux', 'i-linux')),
    'i-simulation',
    'i-validation'
]


def convert_to_datatable_json(dataframe: pd.DataFrame):
    d = json.loads(dataframe.to_json(orient='table'))

    headers = []
    for f_dict in d['schema']['fields']:
        text = str(f_dict['name'])
        value = text.lower().replace(' ', '_')
        headers.append({'text': text, 'value': value})
    items = []
    for d_dict in d['data']:
        i_dict = {}
        for h_map in headers:
            i_dict[h_map['value']] = d_dict[h_map['text']]
        items.append(i_dict)

    return {'headers': headers, 'items': items}


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

                # find node, if not create new one
                node = find_by_attr(parent, name='text', value=name)
                if not node:
                    node = AnyNode(
                        parent=parent, icon=icon, text=name, text_flat=name, selected=False, level=node_data['level'],
                        opened=True,  # if node_data['level'] < 2 else False,
                        id=node_data['obj'].id,
                        klass=type(node_data['obj']).__name__
                    )
                parent = node

        exporter = JsonExporter()
        d = exporter.export(tree)

        # cut off first level, frontend requirement
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
    def get(self, request, *args, **kwargs):
        do_excel = False
        if 'report' in request.GET and request.GET['report'] == 'excel':
            do_excel = True

        grouping = request.GET.get('group-by', 'feature')
        validation_ids = kwargs.get('id', '').split(',')

        validations = Validation.objects.filter(pk__in=validation_ids)
        # Looking for best items in target validations
        ibest = Result.sa \
            .query(Result.sa.item_id, func.max(Status.sa.priority).label('best_status_priority')) \
            .filter(Result.sa.validation_id.in_(validation_ids)
                    , ) \
            .join(Status.sa) \
            .group_by(Result.sa.item_id).subquery('ibest')

        # looking for date of best validation
        best = Result.sa.query(ibest.c.item_id, func.max(Status.sa.id).label('best_status'),
                               func.max(Validation.sa.date).label('best_validation_date')) \
            .select_from(Result.sa) \
            .join(Status.sa, Status.sa.id == Result.sa.status_id).join(Validation.sa,
                                                                       Validation.sa.id == Result.sa.validation_id) \
            .join(ibest, Result.sa.item_id == ibest.c.item_id) \
            .filter(Result.sa.validation_id.in_(validation_ids), Status.sa.priority == ibest.c.best_status_priority) \
            .group_by(ibest.c.item_id).subquery('best')

        v2 = Result.sa.query(Result.sa.item_id, Validation.sa.id, Result.sa.status_id, Validation.sa.date) \
            .filter(Result.sa.validation_id.in_(validation_ids)
                    , ) \
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

        # joining referenced tables to get names and so on
        res = res.subquery('res')
        q = Result.sa.query(
            ResultGroupNew.sa.name.label('group_name') if grouping == 'feature' else ResultGroupNew.sa.alt_name.label(
                'alt_name'),
            Item.sa.name.label('item_name'),
            res.c.best_status_id, Validation.sa.name.label('val_name'), Driver.sa.name.label('driver_name'),
            Result.sa.item_id, Result.sa.validation_id, Validation.sa.source_file, Result.sa.result_url) \
            .select_from(res) \
            .join(Item.sa, Item.sa.id == res.c.item_id) \
            .join(Result.sa, Result.sa.id == res.c.result) \
            .join(ResultGroupNew.sa, ResultGroupNew.sa.id == Item.sa.group_id) \
            .join(Validation.sa) \
            .join(Driver.sa) \
            .order_by(ResultGroupNew.sa.name if grouping == 'feature' else ResultGroupNew.sa.alt_name, Item.sa.name)

        # Create DataFrame crosstab from SQL request
        df = pd.read_sql(q.statement, q.session.bind)
        if df.empty:
            if do_excel:
                return Response()
            return Response({'headers': [], 'items': []})

        ct = pd.crosstab(index=df.group_name if grouping == 'feature' else df.alt_name,
                         values=df.item_name, columns=df.best_status_id, aggfunc='count',
                         colnames=[''],
                         margins=True, margins_name='Total', dropna=False)

        # prepare DataFrame crosstab for response
        ct = prepare_crosstab(ct)
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
    def get(self, request, *args, **kwargs):
        do_excel = False
        if 'report' in request.GET and request.GET['report'] == 'excel':
            do_excel = True
        grouping = request.GET.get('group-by', 'feature')
        validation_ids = kwargs.get('id', '').split(',')
        validations = Validation.objects.filter(pk__in=validation_ids)
        # Looking for last items in target validations with best status priority
        ilast = Result.sa \
            .query(Result.sa.item_id, func.max(Validation.sa.date).label('last_validation_date'),
                   func.max(Status.sa.priority).label('best_status_priority')) \
            .select_from(Result.sa) \
            .join(Validation.sa, Validation.sa.id == Result.sa.validation_id) \
            .join(Status.sa, Status.sa.id == Result.sa.status_id) \
            .filter(Validation.sa.id.in_(validation_ids), ) \
            .group_by(Result.sa.item_id).subquery('ibest')

        vBest = Result.sa \
            .query(ilast.c.item_id, func.max(Result.sa.validation_id).label('last_validation_id'),
                   ilast.c.best_status_priority) \
            .select_from(Result.sa) \
            .join(ilast, Result.sa.item_id == ilast.c.item_id) \
            .join(Validation.sa, Validation.sa.id == Result.sa.validation_id) \
            .filter(Validation.sa.id.in_(validation_ids), Validation.sa.date == ilast.c.last_validation_date) \
            .group_by(ilast.c.item_id, ilast.c.best_status_priority).subquery('vbest')

        res = Result.sa \
            .query(vBest.c.item_id, vBest.c.last_validation_id, func.max(Result.sa.status_id).label('last_status_id'),
                   func.max(Result.sa.id).label('result_id'), vBest.c.best_status_priority) \
            .select_from(vBest) \
            .join(Result.sa,
                  and_(Result.sa.item_id == vBest.c.item_id, Result.sa.validation_id == vBest.c.last_validation_id)) \
            .filter(Result.sa.id.isnot(None)) \
            .group_by(vBest.c.item_id, vBest.c.last_validation_id, vBest.c.best_status_priority)

        # joining referenced tables to get names and so on
        res = res.subquery('res')
        final_query = Result.sa.query(
            ResultGroupNew.sa.name.label('group_name') if grouping == 'feature'
            else ResultGroupNew.sa.alt_name.label('alt_name'),
            Item.sa.name.label('item_name'),
            res.c.last_status_id, Validation.sa.name.label('val_name'), Driver.sa.name.label('driver_name'),
            Result.sa.item_id, Result.sa.validation_id, Validation.sa.source_file, Result.sa.result_url) \
            .select_from(res) \
            .join(Item.sa, Item.sa.id == res.c.item_id) \
            .join(Result.sa, Result.sa.id == res.c.result_id) \
            .join(ResultGroupNew.sa, ResultGroupNew.sa.id == Item.sa.group_id) \
            .join(Validation.sa) \
            .join(Driver.sa) \
            .order_by(ResultGroupNew.sa.name if grouping == 'feature' else ResultGroupNew.sa.alt_name, Item.sa.name)

        # Create DataFrame crosstab from SQL request
        df = pd.read_sql(final_query.statement, final_query.session.bind)
        if df.empty:
            if do_excel:
                return Response()
            return Response({'headers': [], 'items': []})

        ct = pd.crosstab(index=df.group_name if grouping == 'feature' else df.alt_name,
                         values=df.item_name, columns=df.last_status_id, aggfunc='count',
                         colnames=[''],
                         margins=True, margins_name='Total', dropna=False)
        # prepare DataFrame crosstab for response
        ct = prepare_crosstab(ct)
        # If no excel report needed just finish here with json return
        if not do_excel:
            return Response(convert_to_datatable_json(ct))

        # Excel part
        workbook = excel.do_report(data=ct, extra=validations, report_name='Last status report')

        filename = f'last_report_{datetime.now():%Y-%m-%d_%H:%M:%S}.xlsx'
        response = HttpResponse(save_virtual_workbook(workbook), content_type="application/ms-excel")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


def prepare_crosstab(ct: pd.DataFrame):
    all_status_ids = list(Status.objects.all().order_by('priority').values_list('id', flat=True))
    status_mapping = dict(Status.objects.all().values_list('id', 'test_status'))

    # reindex columns by priority and adding notrun and passrate empty ones
    ct = ct.reindex(columns=all_status_ids + ['Total', 'Not run', 'Passrate'])
    ct.rename(columns=status_mapping, inplace=True)
    ct.index.names = ['Group name']  # rename group_name index name

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


class ReportCompareView(LoggingMixin, APIView):
    def get(self, request, *args, **kwargs):
        do_excel = False
        if 'report' in request.GET and request.GET['report'] == 'excel':
            do_excel = True
        options = request.GET.get('show', 'all,show_passed').split(',')
        filtering = options[0]
        show_passed = options[1]

        validation_ids = Validation.objects.filter(id__in=kwargs.get('id', '').split(',')) \
            .order_by('-date').values_list('id', flat=True)

        q = Result.sa \
            .query(func.max(Result.sa.status_id).label('status_id'), Item.sa.name.label('item_name'), Result.sa.item_id,
                   ResultGroupNew.sa.name.label('group_name'), Validation.sa.id.label('validation_id')) \
            .select_from(Result.sa) \
            .filter(Result.sa.validation_id.in_(validation_ids)) \
            .join(Item.sa).join(ResultGroupNew.sa).join(Validation.sa) \
            .group_by(Item.sa.name, Result.sa.item_id, ResultGroupNew.sa.name, Validation.sa.id)

        df = pd.read_sql(q.statement, q.session.bind)
        ct = pd.crosstab(index=[df.item_name], columns=[df.validation_id], values=df.status_id, aggfunc='max')
        ct = ct.replace(np.nan, '', regex=False)

        ct = pd.merge(ct, df, on='item_name', how='outer', right_index=True)
        ct.index.names = ['Item name']  # rename group_name index name
        del ct['status_id']
        del ct['validation_id']
        ct = ct.drop_duplicates()

        # replace status_id with test_status values
        status_mapping = dict(Status.objects.all().values_list('id', 'test_status'))
        for v_id in validation_ids:
            # check if validaton_id column is in DataFrame, i.e. we have items to show for this id
            if v_id in ct:
                ct[v_id] = ct[v_id].map(status_mapping)

        # move item_id and group_id columns to front
        cols = ct.columns.tolist()
        cols = cols[-2:] + list(map(lambda x: int(x), validation_ids))
        ct = ct.reindex(columns=cols)

        # turning validation ids to verbose names
        v_mapping = {}
        v_data = Validation.objects.filter(id__in=validation_ids) \
            .values_list('id', 'name', 'platform__short_name', 'env__name', 'os__name').distinct()
        for d in v_data:
            v_mapping[d[0]] = '{}\n({}, {}, {})'.format(*d[1:])

        ct.rename(columns=v_mapping, inplace=True)

        # renaming, nans to empty strings
        ct.rename(columns={'item_id': 'Item ID', 'group_name': 'Group Name'}, inplace=True)
        ct = ct.replace(np.nan, '', regex=False)

        if filtering == 'diff':
            # drop rows where all statuses are equal
            ct = ct[ct.apply(lambda row: len(row.loc[v_mapping.values()].unique()) > 1, axis=1)]
        elif show_passed == 'hide_passed':
            # drop rows with only passed statuses
            ct = ct[ct.apply(lambda row: (len(row.loc[v_mapping.values()].unique()) > 1
                                          or 'Passed' not in row.loc[v_mapping.values()].unique()), axis=1)]

        # If no excel report needed just finish here with json return
        if not do_excel:
            return Response(convert_to_datatable_json(ct))

        # Excel part
        workbook = excel.do_comparison_report(data=ct)

        filename = f'comparison_report_{datetime.now():%Y-%m-%d_%H:%M:%S}.xlsx'
        response = HttpResponse(save_virtual_workbook(workbook), content_type="application/ms-excel")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


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
            part.validation_ids = Validation.objects \
                                      .filter(env__name__in=[part.env],
                                              platform__short_name__in=[part.platform],
                                              os__name__in=[part.os]) \
                                      .order_by('-date').values_list('id', flat=True)[:part.number]
            if not part.validation_ids:
                hint = f"no validations found for query: {part.env.lower()} " \
                       f"{platform_reverse_map[part.platform]} {part.os.lower()}"
                return Response(data=hint, status=status.HTTP_404_NOT_FOUND)
            validation_ids += part.validation_ids
        recognized_query += ' with'.join(recognized_parts)
        if not validation_ids:
            hint = 'no validations found for query: ' + recognized_query
            return Response(data=hint, status=status.HTTP_404_NOT_FOUND)
        validation_details = []
        validation_data = Validation.objects.filter(pk__in=validation_ids) \
            .values_list('name', 'platform__short_name', 'env__name', 'os__name')
        for d in validation_data:
            validation_details.append('{}\n({}, {}, {})'.format(*d))

        return Response({
            'action': action,
            'description': recognized_query,
            'valnames': validation_details,
            'validation_ids': validation_ids
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
        sender = 'lab_msdk@intel.com'

        msg = EmailMessage(subject, msg, sender, staff_emails, cc=[requester['email']])
        msg.content_subtype = "html"
        try:
            msg.send()
            return Response()
        except Exception:
            return Response(data='Failed to send email', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
