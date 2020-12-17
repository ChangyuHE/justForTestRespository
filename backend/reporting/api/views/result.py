from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from api.models import Result
from api.serializers import ResultFullSerializer, ResultCutSerializer, BulkResultSerializer

from utils.api_logging import LoggingMixin, get_user_object
from utils.api_helpers import UpdateWOutputAPIView

from .filters import ResultsFilter


class ResultView(LoggingMixin, generics.RetrieveAPIView):
    """ List of Result objects """
    queryset = Result.objects.all()
    serializer_class = ResultFullSerializer
    filterset_fields = ['validation_id', 'item_id']


class ResultListView(LoggingMixin, generics.ListAPIView):
    """ List of Result objects by Ids """
    queryset = Result.objects.all()
    serializer_class = ResultFullSerializer
    filterset_class = ResultsFilter


class ResultUpdateView(LoggingMixin, generics.DestroyAPIView, UpdateWOutputAPIView):
    """
    put: Update existing Result object or replace it with new fields
    patch: Update only existing Result's fields
    delete: Delete Result by id
    """
    queryset = Result.objects.all()
    serializer_class = ResultCutSerializer
    serializer_output_class = ResultFullSerializer


class ResultBulkListUpdateView(LoggingMixin, generics.ListAPIView):
    """
    put: Bulk update existing Result object
    """
    serializer_class = BulkResultSerializer

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        ids = [int(item['id']) for item in request.data]

        if ids:
            instances = Result.objects.filter(id__in=ids)
        else:
            raise ValidationError({'integrity error': 'No results for update'})

        serializer = self.get_serializer(
            instances, data=request.data, partial=False, many=True
        )
        serializer.is_valid(raise_exception=True)

        user = get_user_object(request)
        # Change reason for each items is the same
        change_reason = request.data[0]['change_reason']
        self.perform_update(serializer, user, change_reason, *args, **kwargs)

        return Response(serializer.data)

    def perform_update(self, serializer, user, reason, *args, **kwargs):
        serializer.save(_history_user=user, _change_reason=reason, _changed=True)


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

                # do not track changes for bool field '_changed' (internal field)
                if field == '_changed':
                    continue
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
