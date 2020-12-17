from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response

from utils.api_logging import LoggingMixin

from api.models import Validation, Issue
from api.serializers import JiraIssueSerializer


class AssingJiraView(LoggingMixin, APIView):

    def get(self, request: HttpRequest, pk: int, *args, **kwargs) -> Response:
        """
            Return list of Test Items and attached Jira issues
            for validation with id=pk
        """
        validation = get_object_or_404(Validation.objects, pk=pk)

        items = []
        for item in validation.results.values_list(
                        'id',
                        'item__name',
                        'status__test_status',
                        'issues',
                        named=True
                    ):
            for existing in items:
                if existing['c0'] == item.item__name:
                    existing['c2'].append(item.issues)
                    break
            else:
                items.append({
                    'c0': item.item__name,
                    'c1': item.status__test_status,
                    'c2': [item.issues] if item.issues else [],
                    'c3': item.id
                })

        headers = [
            {
                'text': 'Test Item',
                'value': 'c0'
            },
            {
                'text': 'Status',
                'value': 'c1'
            },
            {
                'text': 'Jira Issues',
                'value': 'c2'
            }
        ]

        return Response({'headers': headers, 'items': items, 'total': len(items)})

    def post(
        self,
        request: HttpRequest,
        pk: int,
        test_result_id: int,
        defect_id: str
    ) -> Response:
        """ Add new issue with defect_id to test_result_id """

        validation = get_object_or_404(Validation.objects, pk=pk)
        test_result = get_object_or_404(validation.results, pk=test_result_id)
        test_result.issues.add(defect_id)
        return Response(status=status.HTTP_200_OK)

    def delete(
        self,
        request: HttpRequest,
        pk: int,
        test_result_id: int,
        defect_id: str
    ) -> Response:
        """ Remove issue with defect_id from test_result_id """
        validation = get_object_or_404(Validation.objects, pk=pk)
        test_result = get_object_or_404(validation.results, pk=test_result_id)
        if defect_id in test_result.issues.values_list('name', flat=True):
            test_result.issues.remove(defect_id)
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)


class JiraIssuesView(LoggingMixin, generics.ListAPIView):
    """ List of imported Jira Issues """
    queryset = Issue.objects.exclude(status__startswith='Closed').order_by('-updated')
    serializer_class = JiraIssueSerializer
    filterset_fields = ['name']
