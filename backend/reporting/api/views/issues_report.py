from datetime import datetime
from collections import defaultdict

from django.http import HttpRequest, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response

from openpyxl.writer.excel import save_virtual_workbook

from .. import excel
from api.models import Result
from utils.api_logging import LoggingMixin


class ReportIssuesView(LoggingMixin, APIView):
    def get(self, request: HttpRequest, pk: int, *args, **kwargs):
        do_excel = False
        if 'report' in request.GET and request.GET['report'] == 'excel':
            do_excel = True

        failed = Result.objects.filter(
            validation_id=pk,
            status__test_status='Failed'
        ).values_list(
            'item__name',
            'test_error',
            'additional_parameters__error_features',
            named=True
        ).order_by(
            'additional_parameters__error_features',
            'item__name'
        )

        failed_groups = defaultdict(list)
        for res in failed:
            error_feature: str = res.additional_parameters__error_features
            failed_groups[error_feature].append(
                {'ti': res.item__name, 'err': res.test_error}
            )

        error = Result.objects.filter(
            validation_id=pk,
            status__test_status='Error'
        ).values_list(
            'item__name',
            'result_reason',
            named=True
        ).order_by('result_reason', 'item__name')

        error_groups = defaultdict(list)
        for res in error:
            error_feature: str = res.result_reason
            error_groups[error_feature].append(
                {'ti': res.item__name, 'err': error_feature}
            )

        if not do_excel:
            return Response({'failed': failed_groups, 'error': error_groups})

        workbook = excel.do_issues_report(pk, failed_groups, error_groups)
        filename = f'issues_report_{datetime.now():%Y-%m-%d_%H:%M:%S}.xlsx'
        response = HttpResponse(save_virtual_workbook(workbook),
                                content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
