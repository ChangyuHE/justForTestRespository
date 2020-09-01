from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from .services import import_features
from api.views import LoggingMixin
from utils.api_logging import get_user_object
from utils import api_helpers

from .models import Codec, FeatureCategory, Feature, SubFeature
from .serializers import (CodecSerializer, FeatureCategorySerializer, FeatureSerializer,
                          SubFeatureFullSerializer, SubFeatureIDSerializer)


class ImportView(LoggingMixin, APIView):
    """
    post: Import SubFeatures data from file
    """
    def post(self, request):
        if 'file' not in request.data:
            raise ParseError("'file' parameter is missing in form data.")
        file = request.data['file']
        user = get_user_object(request)
        outcome = import_features(file, user)

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


class SubFeatureUpdateView(LoggingMixin, api_helpers.UpdateWOutputAPIView, generics.DestroyAPIView):
    """
    put: Update existing SubFeature's or replace it with new fields
    patch: Update only existing SubFeature fields
    delete: Delete SubFeature by id
    """
    queryset = SubFeature.objects.all()
    serializer_class = SubFeatureIDSerializer
    serializer_output_class = SubFeatureFullSerializer
