from rest_framework import generics, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.settings import api_settings
from django.db.utils import IntegrityError


def serialiazed_to_datatable_json(serialized, exclude=None, actions=True):
    """ Convert serialized data in dict format to DataTable headers and items """

    if exclude is None:
        exclude = []

    headers, items = [], []
    if not serialized:
        return {'headers': [], 'items': []}

    for field_name, field_value in serialized[0].items():
        if field_name in exclude:
            continue

        # integers (boolean as well) and string values
        if isinstance(field_value, int) or isinstance(field_value, str):
            value = field_name
        elif field_name == 'platform':
            value = 'platform.short_name'
        elif field_name == 'owner':
            value = 'owner.username'
        else:
            value = f'{field_name}.name'

        headers.append({'text': field_name.title(), 'sortable': True, 'value': value})

    if actions:
        headers.append({'text': 'Actions', 'value': 'actions', 'sortable': False, 'width': 10})

    for data in serialized:
        item_data = dict()
        for field_name, field_value in data.items():
            if field_name in exclude:
                continue

            if field_value is not None:
                item_data[field_name] = field_value
            else:
                item_data[field_name] = None

        items.append(item_data)
    return {'headers': headers, 'items': items}


def get_datatable_json(_self, actions=True, exclude=None):
    """ DRF generic API view that returns DataTable formatted json """

    queryset = _self.filter_queryset(_self.get_queryset())
    page = _self.paginate_queryset(queryset)
    if page is not None:
        serializer = _self.get_serializer(page, many=True)
        return _self.get_paginated_response(serializer.data)
    serializer = _self.get_serializer(queryset, many=True)

    return Response(serialiazed_to_datatable_json(serializer.data, actions=actions, exclude=exclude))


class UpdateWOutputAPIView(generics.GenericAPIView):
    """"
    Behaves like rest_framework.generics.UpdateAPIView
    but operates serializer_output_class to represent output data
    """
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            serializer = self.serializer_output_class(serializer.save())
        except IntegrityError:
            raise ValidationError({"integrity error": 'Duplicate creation attempt'})
        except Exception as e:
            raise ValidationError({"detail": e})

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class CreateWOutputApiView(generics.GenericAPIView):
    """"
    Behaves like rest_framework.generics.CreateAPIView
    but operates serializer_output_class to represent output data
    """
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer = self.serializer_output_class(serializer.save())
        except IntegrityError:
            raise ValidationError({"integrity error": 'Duplicate creation attempt'})
        except Exception as e:
            raise ValidationError({"detail": e})

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_success_headers(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}


class DefaultNameOrdering:
    ordering_fields = ['name']
    ordering = ['name']
