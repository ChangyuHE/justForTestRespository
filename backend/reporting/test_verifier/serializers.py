from rest_framework import serializers

from .models import Codec, FeatureCategory, Feature, SubFeature
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
    class Meta:
        model = SubFeature
        fields = '__all__'
