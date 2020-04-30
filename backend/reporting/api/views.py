import copy
import json
import time
import yaml

from pathlib import Path
from collections import defaultdict
from itertools import product
from datetime import datetime
from jinja2 import Environment, PackageLoader

from django.http import HttpResponse
from django.views.generic import TemplateView
from django.shortcuts import render, get_object_or_404
from django.forms.models import model_to_dict
from django.views.decorators.cache import never_cache

from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import *

from reporting.settings import production

from anytree import Node, RenderTree, AnyNode
from anytree.search import find_by_attr
from anytree.exporter import JsonExporter

from sqlalchemy.sql import func
from sqlalchemy.orm import aliased
from sqlalchemy import and_, or_, Table, Column, select, distinct, MetaData, Text, Integer, text, desc, asc

import pandas as pd
import numpy as np

from openpyxl.writer.excel import save_virtual_workbook
from . import excel


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
    (('windows',  'i-windows'), ('linux', 'i-linux')),
    (('windows', 'i-windows'), ('linux', 'i-linux')),
    'i-simulation',
    'i-validation'
]


class ValidationsView(APIView):
    def get(self, request, *args, **kwargs):
        tree = Node('')

        validations_qs = Validation.objects.all().select_related('os__group', 'platform__generation', 'env')
        for validation in validations_qs.order_by('platform__generation__weight', 'platform__weight', 'os__group__name',
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

            parent = tree
            for node_data, icon_map in zip(branch, ICONS):
                # according to ICONS structure detect which icon should be used for each level
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
                        parent=parent, icon=icon, text=name, selected=False,
                        opened=True if node_data['level'] < 2 else False,
                        id=node_data['obj'].id,
                        klass=type(node_data['obj']).__name__
                    )
                parent = node

        exporter = JsonExporter()
        d = exporter.export(tree)

        # cut off first level, frontend requirement
        d = json.loads(d)['children']
        return Response(d)


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


class ReportBestView(APIView):
    def get(self, request, *args, **kwargs):
        do_excel = False
        if 'report' in request.GET and request.GET['report'] == 'excel':
            do_excel = True

        validation_ids = kwargs.get('id', '').split(',')

        validations = Validation.objects.filter(pk__in=validation_ids)
        # print(validations.values_list('name', flat=True))

        # Looking for best items in target validations
        ibest = Result.sa\
            .query(Result.sa.item_id, func.max(Status.sa.priority).label('best_status_priority'))\
            .filter(Result.sa.validation_id.in_(validation_ids)
                    ,)\
            .join(Status.sa)\
            .group_by(Result.sa.item_id).subquery('ibest')
        # print(ibest)

        # looking for date of best validation
        best = Result.sa.query(ibest.c.item_id, func.max(Status.sa.id).label('best_status'), func.max(Validation.sa.date).label('best_validation_date'))\
            .select_from(Result.sa)\
            .join(Status.sa, Status.sa.id == Result.sa.status_id).join(Validation.sa, Validation.sa.id == Result.sa.validation_id) \
            .join(ibest, Result.sa.item_id == ibest.c.item_id) \
            .filter(Result.sa.validation_id.in_(validation_ids), Status.sa.priority == ibest.c.best_status_priority) \
            .group_by(ibest.c.item_id).subquery('best')
        # print(best)

        v2 = Result.sa.query(Result.sa.item_id, Validation.sa.id, Result.sa.status_id, Validation.sa.date)\
            .filter(Result.sa.validation_id.in_(validation_ids)
                    ,)\
            .join(Validation.sa)\
            .subquery('v2')
        # print(v2)

        # Looking for best validation in found date
        vbest = Result.sa.query(best.c.item_id, func.max(v2.c.id).label('best_validation'), func.max(best.c.best_status).label('best_status_id'))\
            .select_from(best)\
            .join(v2, and_(v2.c.item_id == best.c.item_id, v2.c.status_id == best.c.best_status, v2.c.date == best.c.best_validation_date))\
            .group_by(best.c.item_id)\
            .subquery('vbest')

        # Looking for best results in found validations
        res = Result.sa.query(vbest.c.item_id, vbest.c.best_validation, vbest.c.best_status_id, func.max(Result.sa.id).label('result'))\
            .select_from(vbest)\
            .join(Result.sa, and_(Result.sa.item_id == vbest.c.item_id, Result.sa.validation_id == vbest.c.best_validation, Result.sa.status_id == vbest.c.best_status_id))\
            .group_by(vbest.c.item_id, vbest.c.best_validation, vbest.c.best_status_id)

        # print(str(res.statement.compile(compile_kwargs={"literal_binds": True})))
        # print(res.all())

        # joining referenced tables to get names and so on
        res = res.subquery('res')
        q = Result.sa.query(
            ResultGroupNew.sa.name.label('group_name'), Item.sa.name.label('item_name'),
            res.c.best_status_id, Validation.sa.name.label('val_name'), Driver.sa.name.label('driver_name'),
            Result.sa.item_id, Result.sa.validation_id, Validation.sa.source_file, Result.sa.result_url)\
            .select_from(res)\
            .join(Item.sa, Item.sa.id == res.c.item_id)\
            .join(Result.sa, Result.sa.id == res.c.result) \
            .join(ResultGroupNew.sa, ResultGroupNew.sa.id == Item.sa.group_id) \
            .join(Validation.sa)\
            .join(Driver.sa)\
            .order_by(ResultGroupNew.sa.name, Item.sa.name)

        # print(str(q.statement.compile(compile_kwargs={"literal_binds": True})))
        # print(q.all())

        # Create DataFrame crosstab from SQL request
        df = pd.read_sql(q.statement, q.session.bind)
        ct = pd.crosstab(index=df.group_name, values=df.item_name, columns=df.best_status_id, aggfunc='count',
                         colnames=[''],
                         margins=True, margins_name='Total', dropna=False)

        all_status_ids = list(Status.objects.all().order_by('priority').values_list('id', flat=True))
        status_mapping = dict(Status.objects.all().values_list('id', 'test_status'))

        # reindex columns by priority and adding notrun and passrate empty ones
        ct = ct.reindex(columns=all_status_ids + ['Total', 'Not run', 'Passrate'])
        ct.rename(columns=status_mapping, inplace=True)
        ct.index.names = ['Group name']   # rename group_name index name

        # Not run column
        notrun = (ct['Blocked'].fillna(0) + ct['Skipped'].fillna(0) + ct['Canceled'].fillna(0)).round(3).astype(int)
        ct['Not run'] = notrun

        # Passrate column
        passrate = 100 * ct['Passed'].fillna(0) / (ct['Total'] - ct['Not run'])
        ct['Passrate'] = passrate.round(2).astype(str) + '%'

        # leave only needed columns
        ct = ct[['Not run', 'Error', 'Failed', 'Passed', 'Total', 'Passrate']]
        ct = ct.replace(np.nan, '', regex=False).replace(0, '', regex=False)

        if not production:
            print(ct)

        # If no excel report needed just finish here with json return
        if not do_excel:
            d = json.loads(ct.to_json(orient='table'))

            headers = []
            for f_dict in d['schema']['fields']:
                text = f_dict['name']
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
            return Response({'headers': headers, 'items': items})

        # Excel part
        workbook = excel.do_best_report(data=ct, extra=validations)

        filename = f'best_report_{datetime.now():%Y-%m-%d_%H:%M:%S}.xlsx'
        response = HttpResponse(save_virtual_workbook(workbook), content_type="application/ms-excel")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
