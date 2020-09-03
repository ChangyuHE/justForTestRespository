from rest_framework import serializers

from .models import Codec, FeatureCategory, Feature, SubFeature, RuleGroup, Rule
from api.serializers import ComponentSerializer, PlatformSerializer, UserCutSerializer

class CodecSerializer(serializers.ModelSerializer):
    class Meta:
        model = Codec
        fields = ['id', 'name']


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['id', 'name']


class FeatureCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureCategory
        fields = ['id', 'name']


class SubFeatureFullSerializer(serializers.ModelSerializer):
    component = ComponentSerializer(read_only=True)
    codec = CodecSerializer()
    feature = FeatureSerializer()
    category = FeatureCategorySerializer()
    lin_platforms = PlatformSerializer(many=True, read_only=True)
    win_platforms = PlatformSerializer(many=True, read_only=True)
    created_by = UserCutSerializer()
    updated_by = UserCutSerializer()

    class Meta:
        model = SubFeature
        fields = '__all__'


class SubFeatureIDSerializer(serializers.ModelSerializer):
    created_by = UserCutSerializer(read_only=True)
    class Meta:
        model = SubFeature
        fields = '__all__'


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = '__all__'


class RuleGroupFullSerializer(serializers.ModelSerializer):
    rule = RuleSerializer(source='rules', many=True)
    subfeature = SubFeatureFullSerializer()

    class Meta:
        model = RuleGroup
        fields = '__all__'


class RuleGroupIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleGroup
        fields = '__all__'
