from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from .services import import_features
from api.views import LoggingMixin
from utils.api_logging import get_user_object
from utils import api_helpers

from .models import Codec, FeatureCategory, Feature, SubFeature, RuleGroup, Rule
from .serializers import (CodecSerializer, FeatureCategorySerializer, FeatureSerializer,
                          SubFeatureFullSerializer, SubFeatureIDSerializer,
                          RuleGroupFullSerializer, RuleGroupIDSerializer, RuleSerializer)


class ImportView(LoggingMixin, APIView):
    """
    post: Import SubFeatures data from file
    """
    def post(self, request):
        file = request.data.get('file')
        component = request.data.get('component')

        # check for missing parameters
        missing_params = []
        for param_name, value in zip(('file', 'component'), (file, component)):
            if not value or value in ('undefined', 'null'):
                missing_params.append(param_name)
        if missing_params:
            if len(missing_params) == 1:
                msg = f"'{missing_params[0]}' parameter is missing in form data."
            else:
                msg = f"{', '.join(missing_params)} parameters are missing in form data."
            raise ParseError(msg)

        user = get_user_object(request)
        outcome = import_features(file, user, component)

        data = outcome.build()
        code = status.HTTP_200_OK if outcome.is_success() else status.HTTP_422_UNPROCESSABLE_ENTITY

        return Response(data=data, status=code)


class CodecListView(LoggingMixin, generics.ListAPIView):
    """Getting Codec's related full list"""
    queryset = Codec.objects.all()
    serializer_class = CodecSerializer


class FeatureCategoryListView(LoggingMixin, generics.ListAPIView):
    """Getting Feature Categories full list"""
    queryset = FeatureCategory.objects.all()
    serializer_class = FeatureCategorySerializer


class FeatureListView(LoggingMixin, generics.ListAPIView):
    """Getting Feature's full list"""
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer


class SubFeatureListCreateView(LoggingMixin, generics.ListAPIView, api_helpers.CreateWOutputApiView):
    """
    get: Getting SubFeatures full list and full info
    post: Add new SubFeature
    """
    queryset = SubFeature.objects.all().prefetch_related('win_platforms__generation',
                                                         'lin_platforms__generation').select_related()
    serializer_output_class = SubFeatureFullSerializer

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SubFeatureFullSerializer
        return SubFeatureIDSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=get_user_object(self.request))
        return super().perform_create(serializer)


class SubFeatureUpdateView(LoggingMixin, generics.DestroyAPIView, api_helpers.UpdateWOutputAPIView):
    """
    put: Update existing SubFeature or replace it with new fields
    patch: Update only existing SubFeature's fields
    delete: Delete SubFeature by id
    """
    queryset = SubFeature.objects.all()
    serializer_class = SubFeatureIDSerializer
    serializer_output_class = SubFeatureFullSerializer

    def perform_update(self, serializer):
        serializer.save(updated_by=get_user_object(self.request))
        return super().perform_update(serializer)


class RuleListCreateView(LoggingMixin, generics.ListCreateAPIView):
    """
    get: Getting Rules full list and full info
    post: Add new Rule
    """
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer


class RuleUpdateDestroyView(LoggingMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    put: Update existing Rule or replace it with new fields
    patch: Update only existing Rule's fields
    delete: Delete Rule by id
    """
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer


class RuleGroupListCreateView(LoggingMixin, generics.ListCreateAPIView, api_helpers.CreateWOutputApiView):
    """
    get: Getting Rule Groups full list and full info
    post: Add new Rules' Group
    """
    queryset = RuleGroup.objects.all()
    serializer_output_class = RuleGroupFullSerializer

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RuleGroupFullSerializer
        return RuleGroupIDSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=get_user_object(self.request))
        return super().perform_create(serializer)


class RuleGroupsUpdateView(LoggingMixin, generics.DestroyAPIView, api_helpers.UpdateWOutputAPIView):
    """
    put: Update existing Rule Group or replace it with new fields
    patch: Update only existing Rule Group's fields
    delete: Delete Rule Group by id
    """
    queryset = RuleGroup.objects.all()
    serializer_class = RuleGroupIDSerializer
    serializer_output_class = RuleGroupFullSerializer

    def perform_update(self, serializer):
        serializer.save(updated_by=get_user_object(self.request))
        return super().perform_update(serializer)
