from rest_framework import status
from rest_framework.exceptions import ValidationError, ParseError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from django.shortcuts import get_object_or_404

from .models import SubFeature
from .serializers import SubFeatureFullSerializer, SubFeatureIDSerializer
from api.views import LoggingMixin
from .services import import_features


class ImportView(LoggingMixin, APIView):
    """
    post: Import SubFeatures data from file
    """
    def post(self, request):
        if 'file' not in request.data:
            raise ParseError("'file' parameter is missing in form data.")
        file = request.data['file']
        outcome = import_features(file)

        data = outcome.build()
        code = status.HTTP_200_OK if outcome.is_success() else status.HTTP_422_UNPROCESSABLE_ENTITY

        return Response(data=data, status=code)


class SubFeatureListView(LoggingMixin, generics.ListAPIView):
    """ Getting SubFeatures full list and full info """
    queryset = SubFeature.objects.all().prefetch_related('win_platforms__generation',
                                                         'lin_platforms__generation').select_related()
    serializer_class = SubFeatureFullSerializer


class SubFeatureGetDeleteView(LoggingMixin, generics.RetrieveDestroyAPIView):
    """
    get: Get SubFeature info by id
    delete: Delete SubFeature by id
    """
    queryset = SubFeature.objects.all()
    serializer_class = SubFeatureFullSerializer


class SubFeatureUpdateDetailsView(LoggingMixin, generics.GenericAPIView):
    """
    put: Update existing SubFeature's or replace it with new fields
    patch: Update only existing SubFeature fields
    """
    queryset = SubFeature.objects.all()
    serializer_class = SubFeatureIDSerializer

    def put(self, request, pk):
        subfeature = get_object_or_404(SubFeature.objects.all(), pk=pk)
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


class SubFeatureAddView(LoggingMixin, generics.GenericAPIView):
    """
    post: Add new SubFeature
    """
    queryset = SubFeature.objects.all()
    serializer_class = SubFeatureIDSerializer

    def post(self, request):
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