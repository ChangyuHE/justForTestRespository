from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError, ParseError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from django.shortcuts import get_object_or_404

from .models import SubFeature, Codec, Feature, FeatureCategory
from .serializers import SubFeatureFullSerializer, SubFeatureIDSerializer, CodecSerializer, \
    FeatureSerializer, FeatureCategorySerializer
from api.views import LoggingMixin
from api.models import Platform
from api.serializers import PlatformSerializer
from .services import import_features
from utils.api_logging import get_user_object


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


class SubFeatureListView(LoggingMixin, generics.ListCreateAPIView):
    """
        Getting SubFeatures full list and full info
        post: Add new SubFeature
    """
    queryset = SubFeature.objects.all().prefetch_related('win_platforms__generation',
                                                         'lin_platforms__generation').select_related()
    serializer_class = SubFeatureFullSerializer

    def post(self, request):
        request.data['created_by'] = get_user_object(request).id
        request.data['imported'] = False

        input_serializer = SubFeatureIDSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                    {'errors': input_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST)
        try:
            output_serializer = SubFeatureFullSerializer(input_serializer.save())
        except Exception as e:
            raise ValidationError({"detail": e})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class SubFeatureDetailView(LoggingMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    get: Get SubFeature info by id
    delete: Delete SubFeature by id
    put: Update existing SubFeature's or replace it with new fields
    patch: Update only existing SubFeature fields
    """
    queryset = SubFeature.objects.all()
    serializer_class = SubFeatureFullSerializer

    def put(self, request, pk):
        subfeature = get_object_or_404(SubFeature.objects.all(), pk=pk)

        request.data['updated'] = timezone.now().replace(microsecond=0)
        request.data['updated_by'] = get_user_object(request).id
        request.data['imported'] = False

        input_serializer = SubFeatureIDSerializer(instance=subfeature, data=request.data)
        if not input_serializer.is_valid():
            return Response(
                    {'errors': input_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST)
        try:
            output_serializer = SubFeatureFullSerializer(input_serializer.save())
        except Exception as e:
            raise ValidationError({"detail": e})
        return Response(output_serializer.data, status.HTTP_201_CREATED)

    def patch(self, request, pk):
        subfeature = get_object_or_404(SubFeature.objects.all(), pk=pk)

        request.data['updated'] = timezone.now().replace(microsecond=0)
        request.data['updated_by'] = get_user_object(request).id
        request.data['imported'] = False

        input_serializer = SubFeatureIDSerializer(instance=subfeature, data=request.data, partial=True)
        if not input_serializer.is_valid():
            return Response(
                    {'errors': input_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST)
        try:
            output_serializer = SubFeatureFullSerializer(input_serializer.save())
        except Exception as e:
            raise ValidationError({"detail": e})
        return Response(output_serializer.data, status.HTTP_201_CREATED)


class CodecListView(LoggingMixin, generics.ListAPIView):
    queryset = Codec.objects.all()
    serializer_class = CodecSerializer


class CategoryListView(LoggingMixin, generics.ListAPIView):
    queryset = FeatureCategory.objects.all()
    serializer_class = FeatureCategorySerializer


class FeatureListView(LoggingMixin, generics.ListAPIView):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
