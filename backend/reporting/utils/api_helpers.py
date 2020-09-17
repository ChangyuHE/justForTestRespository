from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from rest_framework.serializers import ModelSerializer

from utils.api_logging import get_user_object


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
        if isinstance(field_value, (int, str)):
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


class UpdateWOutputAPIView(generics.UpdateAPIView):
    """"
    Behaves like rest_framework.generics.UpdateAPIView
    but operates serializer_output_class to represent output data
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer = self.perform_update(serializer)
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)

    def perform_update(self, serializer):
        try:
            return self.__class__.serializer_output_class(serializer.save())
        except IntegrityError:
            raise ValidationError({"integrity error": 'Duplicate creation attempt'})
        except Exception as e:
            raise ValidationError({"detail": e})


class CreateWOutputApiView(generics.CreateAPIView):
    """"
    Behaves like rest_framework.generics.CreateAPIView
    but operates serializer_output_class to represent output data
    """
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        try:
            return self.__class__.serializer_output_class(serializer.save())
        except IntegrityError:
            raise ValidationError({"integrity error": 'Duplicate creation attempt'})
        except Exception as e:
            raise ValidationError({"detail": e})


class DefaultNameOrdering:
    ordering_fields = ['name']
    ordering = ['name']


def get_default_owner():
    superusers = get_user_model().objects.filter(is_superuser=True).order_by('pk')
    admin = superusers.filter(username='admin')
    if superusers.exists():
        if admin.exists():
            return admin[0].pk
        return superusers[0].pk
    return 1


def asset_serializer(model):
    """ Returns asset serializer class with fields 'id' and 'url' """
    from api.serializers import AssetUrlSerializer
    return type(f'{model.__name__}Serializer', (AssetUrlSerializer,),
                {'Meta': type('Meta', (object,),
                              {'model': model, 'fields': ['id', 'url']})})


def asset_full_serializer(model):
    """ Returns asset serializer class with all asset fields """
    return type(f'{model.__name__}FullSerializer', (ModelSerializer,),
                {'Meta': type('Meta', (object,),
                              {'model': model, 'fields': '__all__'})})


def model_cut_serializer(model):
    """ Returns serializer class with fields 'name' and 'id' """
    return type(f'{model.__name__}CutSerializer', (ModelSerializer,),
                {'Meta': type('Meta', (object,),
                              {'model': model, 'fields': ['name', 'id']})})


def asset_view(model, full_serializer, out_serializer):
    """ Returns asset view class
        get: List of asset objects (url and id fields)
        post: Create new asset, obtain url field, returns url and id fields
    """
    from api.views import AbstractAssetView
    return type(f'{model.__name__}View', (AbstractAssetView,),
                {'queryset': model.objects.all(),
                 'serializer_class': full_serializer,
                 'serializer_output_class': out_serializer})
