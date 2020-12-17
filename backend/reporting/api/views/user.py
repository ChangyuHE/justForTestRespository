from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from django.db import IntegrityError
from django.contrib.auth import get_user_model

from api.models import Profile
from api.serializers import UserSerializer, ProfileSerializer
from utils.api_logging import get_user_object, LoggingMixin

from .filters import UserSpecificFilterSet


class UserList(LoggingMixin, generics.ListAPIView):
    """ List Users """
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    filterset_class = UserSpecificFilterSet


class CurrentUser(LoggingMixin, APIView):
    """ User's details """

    def get(self, request):
        user_object = get_user_object(request)
        user_data = UserSerializer(user_object).data
        return Response(user_data)


class ProfileView(LoggingMixin, APIView):
    def post(self, request):
        user = get_user_object(request)
        serializer = ProfileSerializer(data=request.data)
        if serializer.is_valid():
            try:
                profile = serializer.save(user=user)
            except IntegrityError:
                raise ValidationError({'integrity error': 'Duplicate creation attempt'})
            except Exception as e:
                raise ValidationError({'detail': e})
            else:
                user.profiles.add(profile)
                return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileDetailsView(LoggingMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def update(self, request, *args, **kwargs):
        to_activate = False
        if 'to_activate' in request.data:
            to_activate = True
            del request.data['to_activate']

        response = super().update(request, *args, **kwargs)
        user = get_user_object(request)
        if to_activate:
            profile_data = response.data
            # set 'active' to false for other profiles
            user.profiles.exclude(id=profile_data['id']).update(active=False)

        # return User data with just updated profile
        return Response(UserSerializer(user).data)

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)
        user = get_user_object(request)
        return Response(UserSerializer(user).data)
