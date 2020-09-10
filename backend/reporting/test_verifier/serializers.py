from django.db import transaction
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

class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = '__all__'

class RuleTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = ['term']

class RuleGroupFullSerializer(serializers.ModelSerializer):
    created_by = UserCutSerializer()
    updated_by = UserCutSerializer()
    rules = RuleSerializer(many=True)

    class Meta:
        model = RuleGroup
        fields = '__all__'


class RuleGroupIDSerializer(serializers.ModelSerializer):
    created_by = UserCutSerializer(read_only=True)
    updated_by = UserCutSerializer(read_only=True)
    rules = RuleTermSerializer(many=True)

    class Meta:
        model = RuleGroup
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        rules_data = validated_data.pop('rules')
        instance = RuleGroup.objects.create(**validated_data)
        self.create_rules(instance, rules_data)

        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        rules_data = validated_data.pop('rules')
        Rule.objects.filter(rule_group=instance).delete()
        self.create_rules(instance, rules_data)

        return super().update(instance, validated_data)

    def create_rules(self, instance, data):
        rules = []
        for rule in data:
            rule = Rule(
                term=rule['term'],
                rule_group=instance
            )
            rules.append(rule)
        Rule.objects.bulk_create(rules)


class SubFeatureFullSerializer(serializers.ModelSerializer):
    component = ComponentSerializer(read_only=True)
    codec = CodecSerializer()
    feature = FeatureSerializer()
    category = FeatureCategorySerializer()
    lin_platforms = PlatformSerializer(many=True, read_only=True)
    win_platforms = PlatformSerializer(many=True, read_only=True)
    created_by = UserCutSerializer()
    updated_by = UserCutSerializer()
    rule_group = RuleGroupFullSerializer(read_only=True)

    class Meta:
        model = SubFeature
        fields = '__all__'


class SubFeatureIDSerializer(serializers.ModelSerializer):
    created_by = UserCutSerializer(read_only=True)
    class Meta:
        model = SubFeature
        fields = '__all__'