import logging

from rest_framework import serializers
from rest_framework import fields
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.exceptions import ValidationError

from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError

import api.models as models
from api.utils.cached_objects_find import parse_item_args, TEST_ITEM_EXTRAS
from utils.api_helpers import model_cut_serializer, asset_serializer, asset_full_serializer

log = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'last_login', 'username', 'first_name', 'last_name', 'email', 'is_staff']


class UserCutSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'fullname']


class EnvSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Env
        fields = ['name', 'short_name']


class KernelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Kernel
        fields = ['name']


class KernelFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Kernel
        fields = ['name', 'id']


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Driver
        fields = ['name']


class DriverFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Driver
        fields = ['name', 'id']


class ComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Component
        fields = ['id', 'name']


class PluginSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Plugin
        fields = ['id', 'name']


class TestScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TestScenario
        fields = ['id', 'name']


class ItemSerializer(serializers.ModelSerializer):
    args = serializers.CharField(trim_whitespace=False, max_length=255)

    class Meta:
        model = models.Item
        fields = ['name', 'args']

    def to_internal_value(self, data):
        """
        Parse item args to get additional plugin, scenario and test_id values
        non-existing plugin and scenario stored as "*__name" fields, existing will have fk ids
        such naming makes possible common django queryset filtering (see create_entities in api/collate/import_api.py)
        """
        validated_data = super().to_internal_value(data)
        validated_data, non_existing = parse_item_args(validated_data)
        for k, v in non_existing.items():
            validated_data[f'{k}__name'] = v

        return validated_data

    @transaction.atomic
    def create(self, validated_data):
        """
        Create Item object using data format produced in to_internal_value
        To create non-existing scenario/plugin "*__name" fields used, then after relations creation their fk ids
        """
        params_to_create = {}
        relations_params = {}

        for field, value in validated_data.items():
            if '__name' in field:  # non existing relation
                field_name = field.split('__')[0]
                model_class = TEST_ITEM_EXTRAS[field_name]['class']
                relations_params[field_name], _ = model_class.objects.get_or_create(name=value)
            else:
                params_to_create[field] = value

        instance = models.Item.objects.get_or_create(**params_to_create, **relations_params)
        return instance


class ItemFullSerializer(serializers.ModelSerializer):
    args = serializers.CharField(trim_whitespace=False, max_length=255)
    plugin = PluginSerializer()
    scenario = TestScenarioSerializer()

    class Meta:
        model = models.Item
        fields = ['name', 'args', 'plugin', 'scenario']


class RunSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Run
        fields = ['name', 'session', 'validation_cycle']


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Status
        fields = ['test_status', 'priority']


class StatusFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Status
        fields = ['test_status', 'priority', 'id']


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


class FeatureMappingSerializer(serializers.ModelSerializer):
    from test_verifier.serializers import CodecSerializer

    codec = CodecSerializer()
    component = ComponentSerializer()
    platform = PlatformSerializer()
    os = OsSerializer()
    owner = UserSerializer()

    class Meta:
        model = models.FeatureMapping
        fields = ['id', 'name', 'owner', 'codec', 'component', 'platform', 'os', 'public', 'official']


class FeatureMappingSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FeatureMapping
        fields = ['name', 'owner', 'codec', 'component', 'platform', 'os', 'public', 'official']
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
        fields = ['id', 'milestone', 'feature', 'scenario', 'mapping', 'ids', 'total']


class FeatureMappingSimpleRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FeatureMappingRule
        fields = ['milestone', 'feature', 'scenario', 'mapping', 'ids', 'total']
        validators = [
            UniqueTogetherValidator(
                queryset=models.FeatureMappingRule.objects.all(),
                fields=['milestone', 'feature', 'scenario', 'mapping', 'ids'],
                message='Duplicate creation attempt'
            ),
        ]


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Asset
        fields = '__all__'


class AssetUrlSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        if not any([obj.root, obj.path, obj.version, obj.name]):
            return 'Empty path'
        if not any([obj.root, obj.path, obj.version]):
            return obj.name
        return str(obj)


# generate template serializers for assets
# cut serializer contains url and id fields, the full one contains all fields
ScenarioAssetSerializer = asset_serializer(models.ScenarioAsset)
ScenarioAssetFullSerializer = asset_full_serializer(models.ScenarioAsset)

LucasAssetSerializer = asset_serializer(models.LucasAsset)
LucasAssetFullSerializer = asset_full_serializer(models.LucasAsset)

MsdkAssetSerializer = asset_serializer(models.MsdkAsset)
MsdkAssetFullSerializer = asset_full_serializer(models.MsdkAsset)

FulsimAssetSerializer = asset_serializer(models.FulsimAsset)
FulsimAssetFullSerializer = asset_full_serializer(models.FulsimAsset)

OsAssetSerializer = asset_serializer(models.OsAsset)


# generate template cut serializers which contains 'id' and 'name' fields
ValidationCutSerializer = model_cut_serializer(models.Validation)
EnvCutSerializer = model_cut_serializer(models.Env)
ComponentCutSerializer = model_cut_serializer(models.Component)
OsCutSerializer = model_cut_serializer(models.Os)


class PlatformCutSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Platform
        fields = ['short_name', 'id']


class SimicsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Simics
        fields = '__all__'


class ResultFullSerializer(serializers.ModelSerializer):
    validation = ValidationCutSerializer()
    driver = DriverFullSerializer()
    item = ItemFullSerializer()
    component = ComponentCutSerializer()
    env = EnvCutSerializer()
    platform = PlatformCutSerializer()
    os = OsCutSerializer()
    kernel = KernelFullSerializer()
    status = StatusFullSerializer()
    run = RunSerializer()

    scenario_asset = ScenarioAssetSerializer()
    msdk_asset = MsdkAssetSerializer()
    os_asset = OsAssetSerializer()
    lucas_asset = LucasAssetSerializer()
    fulsim_asset = FulsimAssetSerializer()
    simics = SimicsSerializer()

    class Meta:
        model = models.Result
        fields = '__all__'


class ResultCutSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Result
        fields = '__all__'


class BulkUpdateListSerializer(serializers.ListSerializer):

    def update(self, instances, validated_data):
        result = [self.child.update(instance, attrs) for instance, attrs in zip(instances, validated_data)]

        writable_fields = [
            field
            for field in self.child.Meta.fields
            if field not in self.child.Meta.read_only_fields
        ]

        try:
            self.child.Meta.model.objects.bulk_update(result, writable_fields)
        except IntegrityError as e:
            raise ValidationError(e)

        return result


class BulkResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Result
        fields = ['id', 'item', 'status', 'driver', 'scenario_asset', 'lucas_asset', 'msdk_asset', 'fulsim_asset', 'simics']
        read_only_fields = ['id', 'item']
        list_serializer_class = BulkUpdateListSerializer
