from rest_framework import serializers

from .models import SubFeature, Codec, Feature, FeatureCategory


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
    from api.serializers import PlatformSerializer

    codec = CodecSerializer()
    feature = FeatureSerializer()
    category = FeatureCategorySerializer()
    lin_platforms = PlatformSerializer(many=True, read_only=True)
    win_platforms = PlatformSerializer(many=True, read_only=True)

    class Meta:
        model = SubFeature
        fields = '__all__'


class SubFeatureIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubFeature
        fields = '__all__'
