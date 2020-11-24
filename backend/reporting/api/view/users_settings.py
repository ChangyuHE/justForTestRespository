from rest_framework import generics, status, filters
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api.models import Profile
from api.serializers import ProfileSerializer

from utils.api_logging import get_user_object, LoggingMixin
from utils.api_helpers import get_datatable_json, DefaultNameOrdering, CreateWOutputApiView, \
    UpdateWOutputAPIView


class ProfileView(LoggingMixin, APIView):
    pass
