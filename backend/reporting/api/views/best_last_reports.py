import json
from datetime import datetime
from typing import Optional, List

import pandas as pd
import numpy as np

from django.http import HttpRequest, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response

from sqlalchemy import and_
from sqlalchemy.sql import func

from openpyxl.writer.excel import save_virtual_workbook

from api.models import Validation, Result, Status, Item, Driver
from utils.api_logging import LoggingMixin

from .. import excel
from .common_functions import fmt_rules


__all__ = ['ReportBestView', 'ReportLastView']


class ReportBestView(LoggingMixin, APIView):
    def get(self, request: HttpRequest, val_pks: List[int], fmt_pks: Optional[List[int]] = None,
            *args, **kwargs) -> Response:
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
            .filter(
                Result.sa.validation_id.in_(val_pks),
                Status.sa.priority == ibest.c.best_status_priority) \
            .group_by(ibest.c.item_id).subquery('best')

        v2 = Result.sa.query(
                Result.sa.item_id,
                Validation.sa.id,
                Result.sa.status_id, Validation.sa.date
            ) \
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
                  and_(
                      Result.sa.item_id == vbest.c.item_id,
                      Result.sa.validation_id == vbest.c.best_validation,
                      Result.sa.status_id == vbest.c.best_status_id
                    )
                ) \
            .group_by(vbest.c.item_id, vbest.c.best_validation, vbest.c.best_status_id)

        # Select scenario ids, feature names, codec names from
        # feature mapping rules which belong to selected FMTs
        fm_rules = fmt_rules(fmt_pks).subquery('fm_rules')

        # joining referenced tables to get names and so on
        res = res.subquery('res')
        q = Result.sa.query(
            (fm_rules.c.Feature if grouping == 'feature' else fm_rules.c.Codec).label('group'),
            Item.sa.name.label('item_name'), fm_rules.c.Codec,
            res.c.best_status_id, Validation.sa.name.label('val_name'),
            Driver.sa.name.label('driver_name'), Result.sa.item_id, Result.sa.validation_id,
            Validation.sa.source_file, Result.sa.result_url) \
                .select_from(res) \
                .join(Item.sa, Item.sa.id == res.c.item_id) \
                .join(Result.sa, Result.sa.id == res.c.result) \
                .join(fm_rules, Item.sa.scenario_id == fm_rules.c.scenario_id, full=True) \
                .join(Validation.sa) \
                .join(Driver.sa) \
                .order_by(fm_rules.c.Feature if grouping == 'feature' else fm_rules.c.Codec,
                        Item.sa.name)

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
        response = HttpResponse(save_virtual_workbook(workbook), content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ReportLastView(LoggingMixin, APIView):
    def get(self, request: HttpRequest, val_pks: List[int], fmt_pks: Optional[List[int]] = None,
            *args, **kwargs) -> Response:
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

        # Select last status ids and last result ids for items
        # from last validations with best status priority
        res = Result.sa \
            .query(vBest.c.item_id, vBest.c.last_validation_id,
                func.max(Result.sa.status_id).label('last_status_id'),
                func.max(Result.sa.id).label('result_id'),
                vBest.c.best_status_priority) \
            .select_from(vBest) \
            .join(Result.sa,
                  and_(Result.sa.item_id == vBest.c.item_id,
                  Result.sa.validation_id == vBest.c.last_validation_id)) \
            .filter(Result.sa.id.isnot(None)) \
            .group_by(vBest.c.item_id, vBest.c.last_validation_id, vBest.c.best_status_priority)

        # Select scenario ids, feature names, codec names from
        # feature mapping rules which belong to selected FMTs
        fm_rules = fmt_rules(fmt_pks).subquery('fm_rules')

        # joining referenced tables to get names and so on
        res = res.subquery('res')
        final_query = Result.sa.query(
            (fm_rules.c.Feature if grouping == 'feature' else fm_rules.c.Codec).label('group'),
            Item.sa.name.label('item_name'), fm_rules.c.Codec,
            res.c.last_status_id, Validation.sa.name.label('val_name'),
            Driver.sa.name.label('driver_name'),
            Result.sa.item_id, Result.sa.validation_id, Validation.sa.source_file,
            Result.sa.result_url) \
                .select_from(res) \
                .join(Item.sa, Item.sa.id == res.c.item_id) \
                .join(Result.sa, Result.sa.id == res.c.result_id) \
                .join(fm_rules, Item.sa.scenario_id == fm_rules.c.scenario_id, full=True) \
                .join(Validation.sa) \
                .join(Driver.sa) \
                .order_by(fm_rules.c.Feature if grouping == 'feature' else fm_rules.c.Codec,
                    Item.sa.name)

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
        response = HttpResponse(save_virtual_workbook(workbook), content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


def prepare_crosstab(ct: pd.DataFrame, grouping: str):
    all_status_ids = list(Status.objects.all().order_by('priority').values_list('id', flat=True))
    status_mapping = dict(Status.objects.all().values_list('id', 'test_status'))

    # reindex columns by priority and adding notrun and passrate empty ones
    ct = ct.reindex(columns=all_status_ids + ['Total', 'Not run', 'Passrate'])
    ct.rename(columns=status_mapping, inplace=True)

    # rename group_name index name
    ct.index.names = ['Feature'] if grouping == 'feature' else ['Codec']

    # Not run column
    notrun = (
        ct['Blocked'].fillna(0) +
        ct['Skipped'].fillna(0) +
        ct['Canceled'].fillna(0)).round(3).astype(int)

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
