import json
import pandas as pd
import numpy as np
import dateutil.parser

from datetime import datetime

from django.http import HttpResponse
from django.views.generic import TemplateView
from django.shortcuts import render, get_object_or_404
from django.forms.models import model_to_dict
from django.views.decorators.cache import never_cache
from django.db import transaction

from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response

from anytree import Node, RenderTree, AnyNode
from anytree.search import find_by_attr
from anytree.exporter import JsonExporter

from sqlalchemy.sql import func
from sqlalchemy.orm import aliased
from sqlalchemy import and_, or_, Table, Column, select, distinct, MetaData, Text, Integer, text, desc, asc

from openpyxl.writer.excel import save_virtual_workbook

from . import excel
from .models import *

from reporting.settings import production


@never_cache
def index(request):
    return render(request, 'api/index.html', {})


# all requests that should managed by vue just pass to index
class PassToVue(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'api/index.html', {})


ICONS = [
    'i-gen',
    'i-platform',
    (('windows', 'i-windows'), ('linux', 'i-linux')),
    (('windows', 'i-windows'), ('linux', 'i-linux')),
    'i-simulation',
    'i-validation'
]


def convert_to_datatable_json(dataframe):
    d = json.loads(dataframe.to_json(orient='table'))

    headers = []
    for f_dict in d['schema']['fields']:
        text = str(f_dict['name'])
        value = text.lower().replace(' ', '_')
        headers.append({'text': text, 'value': value})
    # print(headers)

    items = []
    for d_dict in d['data']:
        i_dict = {}

        for h_map in headers:
            i_dict[h_map['value']] = d_dict[h_map['text']]
        items.append(i_dict)
    # print(items)
    return {'headers': headers, 'items': items}


class ValidationsView(APIView):
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


class ValidationsDeleteByIdView(generics.DestroyAPIView):
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


class ValidationsFlatView(APIView):
    def get(self, request, *args, **kwargs):
        d = []
        validations_qs = Validation.objects.all().order_by('-id')
        for v in validations_qs:
            d.append({
                'name': f'{v.name} ({v.platform.name}, {v.env.name}, {v.os.name})',
                'id': v.id
            })
        return Response(d)


class ValidationsStructureView(APIView):
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


class ReportBestView(APIView):
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


class ReportLastView(APIView):
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


class ReportCompareView(APIView):
    def get(self, request, *args, **kwargs):
        do_excel = False
        if 'report' in request.GET and request.GET['report'] == 'excel':
            do_excel = True
        options = request.GET.get('show', 'all,show_passed').split(',')
        filtering = options[0]
        show_pased = options[1]

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
            ct[int(v_id)] = ct[int(v_id)].map(status_mapping)

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
        elif show_pased == 'hide_passed':
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
