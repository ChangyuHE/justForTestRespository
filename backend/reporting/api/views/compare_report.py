import re
import json
from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd
import numpy as np

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response

from sqlalchemy.sql import func
from sqlalchemy.orm import Query

from openpyxl.writer.excel import save_virtual_workbook

from api.models import Validation, Result, Item, Status

from utils.api_logging import LoggingMixin

from .. import excel
from .common_functions import fmt_rules


__all__ = ['ReportCompareView', 'ExtraDataView']


class ReportCompareView(LoggingMixin, APIView):
    def get(self, request: HttpRequest, val_pks: List[int], fmt_pks: Optional[List[int]] = None,
            *args, **kwargs) -> Response:
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
            mask = statuses.apply(
                lambda row: (len(row.loc[val_pks].unique()) > 1 or
                            'Passed' not in row.loc[val_pks].unique()), axis=1)
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
        statuses.set_index('Item name', inplace=True)

        # If no excel report needed just finish here with json return
        if not do_excel:
            return Response(create_json_for_datatables(statuses, result_ids, id_to_name, total))

        # Excel part
        workbook = excel.do_comparison_report(statuses)

        filename = f'comparison_report_{datetime.now():%Y-%m-%d_%H:%M:%S}.xlsx'
        response = HttpResponse(save_virtual_workbook(workbook), content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
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
                    'os': val.os.name,
                    'env': val.env.name
                }
            else:
                res = get_object_or_404(Result, pk=int(res_pk))
                item_name = res.item.name
                val = res.validation
                datum['vinfo'] = {
                    'validation': val.name,
                    'platform': val.platform.short_name,
                    'os': val.os.name,
                    'env': val.env.name
                }
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
                datum['main_info'] = {
                    'status': res.status.test_status,
                    'job link': str(res.result_url),
                    'build version': str(res.driver),
                    'kernel version': str(res.kernel.name) if res.kernel else '',
                    'kernel update date': str(res.kernel.updated_date) if res.kernel else ''
                }
            extra_data.append(datum)

        try:
            extra_data = _calculate_metric_diff(extra_data)
        except (KeyError, ValueError, TypeError):
            # to do not affect main extra data actions
            pass

        return Response({
            'item': item_name,
            'extra': extra_data
        })


def create_json_for_datatables(
        statuses: pd.DataFrame,
        result_ids: pd.DataFrame,
        id_to_name: Dict[int, str],
        total: int,
    ):
    reverse_map = {v: k for k, v in id_to_name.items()}
    val_pks = id_to_name.keys()
    d = json.loads(statuses.to_json(orient='table'))
    headers = []
    for i, field in enumerate(d['schema']['fields']):
        text = str(field['name'])
        value = f'f{i}'
        headers.append({'text': text, 'value': value})

    result_ids = json.loads(result_ids.to_json(orient='table'))

    items = []
    _results = list(Result.objects.filter(validation_id__in=val_pks))
    changed_results = [result.id for result in _results if result._changed]
    for statuses, results in zip(d['data'], result_ids['data']):
        item = {}

        # result ids list to get similar marker
        ids = [result_id for key, result_id in results.items() if key != 'Item ID']
        instances = [result for result in _results if result.id in ids]
        if len(instances) > 1:
            # reference instance from the first validation
            reference_instance = instances[0]
            different = [res for res in instances[1:] if not reference_instance.similar(res)]
            item['is_similar'] = not different

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
                            if result_id in changed_results:
                                status_dict['changed'] = True
                            status_dict['tiId'] = result_id
                            del status_dict['valId']
                item[key] = status_dict

        items.append(item)

    return {'headers': headers, 'items': items, 'total': total}


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
    feature_and_codec = df.loc[df['scenario_id'] == row.scenario_id]
    if not feature_and_codec.empty:
        # to prevent strange effect with list of single
        # element inside...
        row['Feature'] = feature_and_codec['Feature'].values[0]
        row['Codec'] = feature_and_codec['Codec'].values[0]

    return row


def replace_item_id(row: pd.Series, items_dict: Dict[int, str]) -> pd.Series:
    row['Item name'] = items_dict[row['Item name']]
    return row


def validation_statuses(validation_ids: List[int], fmt_pks: List[int]) -> pd.DataFrame:
    q = Result.sa \
        .query(func.max(Result.sa.status_id).label('status_id'),
                Item.sa.test_id, Item.sa.scenario_id, Result.sa.item_id, Item.sa.id,
                Validation.sa.id.label('validation_id')) \
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


def _calculate_metric_diff(
        extra_data: List[Dict[str, Dict[str, str]]]) -> List[Dict[str, Dict[str, str]]]:
    """
    Calculate difference for extra data view between numeric metrics
    :param extra_data: result data of all compared validations
    :return: modified extra_data with added metric difference calculations
    """
    if len(extra_data) < 2:
        return extra_data

    def _is_digit(value: str) -> bool:
        if value.isdigit() or value.replace('.', '', 1).isdigit():
            return True
        return False

    metrics_key = 'additional_parameters'
    for i, extra in enumerate(extra_data[:-1]):
        if metrics_key not in extra:
            continue
        # first filled selected validation as a base for comparison of metrics
        compared_data = extra_data[i][metrics_key]

        # next others full-filled to compare
        for ti_data in extra_data[i + 1:]:
            if metrics_key not in ti_data:
                continue
            for metric, m in ti_data[metrics_key].items():
                if m and metric in compared_data:
                    # prepare metrics for calc:
                    # change comma to float point / drop byte 'B' suffix for diff
                    compared_m = compared_data[metric].replace(',', '.').replace('B', '').strip()
                    m = m.replace(',', '.').replace('B', '').strip()
                    if _is_digit(m) and _is_digit(compared_m):
                        diff: float = float(m) - float(compared_m)
                        if diff == 0.0:
                            diff: str = ''
                        elif diff.is_integer():
                            diff: int = int(diff)
                            diff: str = f' ({diff:+})'
                        else:
                            diff: str = f' ({diff:+.6f})'
                            # remove trailing zeroes for floating values if exist
                            diff: str = re.sub(r'(0+)\)$', ')', diff)
                        ti_data[metrics_key][metric] += diff
        if compared_data:
            break

    return extra_data
