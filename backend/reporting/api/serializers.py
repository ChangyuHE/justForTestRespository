import logging

from rest_framework import serializers
from rest_framework import fields
from rest_framework.validators import UniqueTogetherValidator

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
        fields = ['id', 'name']


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Item
        fields = ['name', 'args', 'group']
        validators = [
            UniqueTogetherValidator(
                queryset=models.Item.objects.all(),
                fields=['name', 'args']
            )
        ]


class RunSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Run
        fields = ['name', 'session', 'validation_cycle']


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Status
        fields = ['test_status', 'priority']


class GenerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Generation
        fields = ['id', 'name']


class PlatformSerializer(serializers.ModelSerializer):
    generation = GenerationSerializer()

    class Meta:
        model = models.Platform
        fields = ['id', 'name', 'generation', 'aliases', 'short_name', 'weight', 'planning']


class OsSerializer(serializers.ModelSerializer):
    parent_os = serializers.SerializerMethodField()

    def get_parent_os(self, obj):
        if obj.group is not None:
            return OsSerializer(obj.group).data
        return None

    class Meta:
        model = models.Os
        fields = ['id', 'name', 'group', 'weight', 'aliases', 'parent_os']


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


# FeatureMapping block
class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Milestone
        fields = ['id', 'name']


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Feature
        fields = ['id', 'name']


class TestScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TestScenario
        fields = ['id', 'name']


class FeatureMappingSerializer(serializers.ModelSerializer):
    component = ComponentSerializer()
    platform = PlatformSerializer()
    os = OsSerializer()
    owner = UserSerializer()

    class Meta:
        model = models.FeatureMapping
        fields = ['id', 'name', 'owner', 'component', 'platform', 'os', 'public', 'official']


class FeatureMappingSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FeatureMapping
        fields = ['name', 'owner', 'component', 'platform', 'os', 'public', 'official']
        validators = [
            UniqueTogetherValidator(
                queryset=models.FeatureMapping.objects.all(),
                fields=['name', 'owner']
            )
        ]


class FeatureMappingRuleSerializer(serializers.ModelSerializer):
    milestone = MilestoneSerializer()
    feature = FeatureSerializer()
    scenario = TestScenarioSerializer()

    class Meta:
        model = models.FeatureMappingRule
        fields = ['id', 'milestone', 'feature', 'scenario', 'mapping']


class FeatureMappingSimpleRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FeatureMappingRule
        fields = ['milestone', 'feature', 'scenario', 'mapping']
        validators = [
            UniqueTogetherValidator(
                queryset=models.FeatureMappingRule.objects.all(),
                fields=['milestone', 'feature', 'scenario', 'mapping']
            )
        ]
