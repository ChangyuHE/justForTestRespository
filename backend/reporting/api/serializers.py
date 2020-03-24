from .models import *

from rest_framework import serializers
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from rest_framework.utils import model_meta


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = get_user_model()
#         fields = ['id', 'last_login', 'username', 'first_name', 'last_name', 'email', 'is_staff']
