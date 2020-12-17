import copy
from typing import Dict
from datetime import datetime
from collections import defaultdict

from django.db.models import Case, When
from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.response import Response

from openpyxl.writer.excel import save_virtual_workbook

from api.models import Validation, Result, FeatureMapping, FeatureMappingRule

from .. import excel


class ReportIndicatorView(APIView):
    def get(self, request, id, *args, **kwargs):
        def update_status(current: Dict[str, int], total: Dict[str, int], status: str):
            current[status.lower()] += 1
            total[status.lower()] += 1

            if status in ('Skipped', 'Blocked', 'Canceled'):
                current['notrun'] += 1
                total['notrun'] += 1

        # main body
        mapping_ids = request.GET.get('fmt_id').split(',')

        # ensure that mode has one of two possible values
        mode = request.GET.get('mode', 'single')
        if mode not in ('single', 'combined'):
            mode = 'single'

        do_excel = False
        if 'report' in request.GET and request.GET['report'] == 'excel':
            do_excel = True

        data = defaultdict(dict)
        total_counters = {
            'passed': 0,
            'failed': 0,
            'error': 0,
            'blocked': 0,
            'skipped': 0,
            'canceled': 0,

            'passrate': 0,
            'execrate': 0,

            'notrun': 0,
            'total': 0
        }

        results = Result.objects.filter(validation_id=id)
        # get mappings with preserved ids order from request
        original_order = Case(*[When(pk=pk, then=position)
                                for position, pk in enumerate(mapping_ids)])
        mappings = FeatureMapping.objects.filter(pk__in=mapping_ids).order_by(original_order)

        for mapping in mappings:
            mapping_data = defaultdict(dict)
            mapping_total = {
                'passed': 0,
                'failed': 0,
                'error': 0,
                'blocked': 0,
                'skipped': 0,
                'canceled': 0,

                'passrate': 0,
                'execrate': 0,

                'notrun': 0,
                'total': 0
            }

            for milestone, scenario_id, feature, ids, total_value in \
                FeatureMappingRule.objects.filter(mapping_id=mapping.id) \
                    .values_list('milestone__name', 'scenario_id', 'feature__name', 'ids', 'total'):
                if mode == 'combined':
                    feature_name = f'{feature} ({mapping.codec.name})'
                else:
                    feature_name = feature

                if ids is not None:
                    total_value = len(ids.split(','))

                mapping_data[milestone][feature_name] = {
                    'passed': 0,
                    'failed': 0,
                    'error': 0,
                    'blocked': 0,
                    'skipped': 0,
                    'canceled': 0,

                    'passrate': 0,
                    'execrate': 0,

                    'notrun': 0,
                    'total': total_value
                }

                # show Indicator report even if FMT is incorrect i.e. it does
                # not have total value set
                if total_value is None:
                    total_value = 0

                mapping_total['total'] += total_value

                if ids is not None:
                    ids = ids.split(',')
                    executed = results.filter(item__scenario_id=scenario_id,
                                              item__test_id__in=ids).count()
                    for status in results.filter(item__scenario_id=scenario_id,
                                                 item__test_id__in=ids) \
                            .values_list('status__test_status', flat=True):
                        update_status(mapping_data[milestone][feature_name], mapping_total, status)
                else:
                    executed = results.filter(item__scenario_id=scenario_id).count()
                    for status in results.filter(item__scenario_id=scenario_id) \
                            .values_list('status__test_status', flat=True):
                        update_status(mapping_data[milestone][feature_name], mapping_total, status)

                not_executed = total_value - executed

                # protect ourselves from broken FMTs which have None
                # in total column and total = 0
                if not_executed > 0:
                    mapping_data[milestone][feature_name]['notrun'] += not_executed
                    mapping_total['notrun'] += not_executed

                passed = mapping_data[milestone][feature_name]['passed']
                total = mapping_data[milestone][feature_name]['total']
                not_run = mapping_data[milestone][feature_name]['notrun']

                mapping_data[milestone][feature_name]['passrate'] = passed / total
                mapping_data[milestone][feature_name]['execrate'] = (total - not_run) / total

            if mode == 'single' and do_excel:
                # split data by mappings
                data[mapping.id]['items'] = copy.deepcopy(mapping_data)
                data[mapping.id]['total'] = copy.deepcopy(mapping_total)
            else:
                # merge to one dict
                for key, value in mapping_data.items():
                    for subkey, subvalue in value.items():
                        data[key][subkey] = subvalue

                for key in ['total',
                            'passed',
                            'failed',
                            'error',
                            'blocked',
                            'skipped',
                            'canceled',
                            'notrun']:
                    total_counters[key] += mapping_total[key]

                total_counters['passrate'] = total_counters['passed'] / total_counters['total']
                total_counters['execrate'] = (total_counters['total'] -
                                              total_counters['notrun']) / total_counters['total']

        if not data:
            if do_excel:
                return Response()
            return Response({'headers': [], 'items': []})

        if not do_excel:
            # Data-table formatting
            headers, items = [], []
            for label in ('Milestone',
                          'Feature',
                          'Total',
                          'Passed',
                          'Failed',
                          'Error',
                          'Blocked',
                          'Skipped',
                          'Canceled',
                          'Not Run',
                          'Pass Rate',
                          'Exec Rate'):
                headers.append({
                    'text': label,
                    'value': label.replace(' ', '').lower(),
                    'groupable': True if label == 'Milestone' else False,
                    'width': 140 if label not in ('Milestone', 'Feature') else None,
                })

            for milestone, m_data in data.items():
                for feature, f_data in m_data.items():
                    items.append({'milestone': milestone, 'feature': feature, **f_data})
            items.append(total_counters)

            return Response({'headers': headers, 'items': items})
        else:
            # Excel part
            validation = Validation.objects.get(id=id)

            if mode == 'combined':
                excel_data = {'items': data, 'total': total_counters}
            else:
                excel_data = data
            workbook = excel.do_indicator_report(excel_data, validation, mappings, mode)
            filename = f'indicator_report_{datetime.now():%Y-%m-%d_%H:%M:%S}.xlsx'
            response = HttpResponse(save_virtual_workbook(workbook),
                                    content_type='application/ms-excel')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
