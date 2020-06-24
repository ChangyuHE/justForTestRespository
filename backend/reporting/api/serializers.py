import logging

from rest_framework import serializers
from rest_framework import fields

from django.contrib.auth import get_user_model

import api.models as models

log = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'last_login', 'username', 'first_name', 'last_name', 'email', 'is_staff']


class EnvSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Env
        fields = ['name', 'short_name']


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Driver
        fields = ['name']


class ComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Component
        fields = ['name']


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Item
        fields = ['name', 'args', 'group']


class RunSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Run
        fields = ['name', 'session', 'validation_cycle']


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Status
        fields = ['test_status', 'priority']


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Platform
        fields = ['name', 'generation', 'aliases', 'short_name', 'weight', 'planning']


class OsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Os
        fields = ['name', 'group', 'aliases', 'planning']


def create_serializer(class_name, instance=None, data=fields.empty, **kwargs):
    if class_name == 'Env':
        return EnvSerializer(instance, data, **kwargs)
    elif class_name == 'Driver':
        return DriverSerializer(instance, data, **kwargs)
    elif class_name == 'Component':
        return ComponentSerializer(instance, data, **kwargs)
    elif class_name == 'Item':
        return ItemSerializer(instance, data, **kwargs)
    elif class_name == 'Run':
        return RunSerializer(instance, data, **kwargs)
    elif class_name == 'Status':
        return StatusSerializer(instance, data, **kwargs)
    elif class_name == 'Platform':
        return PlatformSerializer(instance, data, **kwargs)
    elif class_name == 'Os':
        return OsSerializer(instance, data, **kwargs)
    else:
        log.warning(f"Serializer for class '{class_name}' is not defined.'")
        return None
