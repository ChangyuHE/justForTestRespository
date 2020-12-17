import itertools

from django.contrib.auth import get_user_model
from django_filters import rest_framework

from api.models import Result, Status, ResultFeature, Component, Validation


class NumberInFilter(rest_framework.BaseInFilter, rest_framework.NumberFilter):
    pass


class CharInFilter(rest_framework.BaseInFilter, rest_framework.CharFilter):
    pass


class UserSpecificFilterSet(rest_framework.FilterSet):
    validations = rest_framework.BooleanFilter(
        field_name='validations',
        method='validations_empty'
    )
    ids__in = NumberInFilter(field_name='id', lookup_expr='in')

    def validations_empty(self, queryset, _, value):
        return queryset \
                .filter(**{'validations__isnull': not value}) \
                .distinct('id')

    class Meta:
        model = get_user_model()
        fields = ['validations', 'is_staff', 'username', 'ids__in']


class ResultsFilter(rest_framework.FilterSet):
    ids__in = NumberInFilter(field_name='id', lookup_expr='in')

    class Meta:
        model = Result
        fields = ['ids__in']


class StatusFilter(rest_framework.FilterSet):
    test_status__in = CharInFilter(field_name='test_status', lookup_expr='in')

    class Meta:
        model = Status
        fields = ['test_status__in']


class ResultFeatureFilter(rest_framework.FilterSet):
    active = rest_framework.BooleanFilter(
        field_name='id',
        method='is_active'
    )

    def is_active(self, queryset, name, _):
        # get list of features in all validations
        features = set(
            # flatten list of lists
            itertools.chain.from_iterable(
                list(
                    Validation.objects.values_list(
                        'features',
                        flat=True).distinct()
                    )
            )
        )
        return queryset.filter(id__in=sorted(features))

    class Meta:
        model = ResultFeature
        fields = ['active', 'name']


class ComponentFilter(rest_framework.FilterSet):
    active = rest_framework.BooleanFilter(
        field_name='id',
        method='is_active'
    )

    def is_active(self, queryset, name, _):
        # get list of components in all validations
        components = set(
            # flatten list of lists
            itertools.chain.from_iterable(
                list(
                    Validation.objects.values_list(
                        'components',
                        flat=True).distinct()
                    )
                )
        )
        return queryset.filter(id__in=sorted(components))

    class Meta:
        model = Component
        fields = ['active', 'name']
