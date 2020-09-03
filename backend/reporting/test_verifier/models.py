from django.db import models
from django.db.models import UniqueConstraint

from api.models import Platform, Component

from reporting.settings import AUTH_USER_MODEL


class Codec(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class FeatureCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = 'Feature Categories'

    def __str__(self):
        return self.name


class Feature(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class SubFeature(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(FeatureCategory, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    codec = models.ForeignKey(Codec, on_delete=models.CASCADE)
    component = models.ForeignKey(Component, on_delete=models.PROTECT)
    lin_platforms = models.ManyToManyField(Platform, related_name='lin_subfeatures', blank=True)
    win_platforms = models.ManyToManyField(Platform, related_name='win_subfeatures', blank=True)
    notes = models.CharField(max_length=255, blank=True, null=True)
    imported = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_subfeatures')
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.ForeignKey(AUTH_USER_MODEL, blank=True, null=True,
                                   on_delete=models.PROTECT, related_name='updated_subfeatures')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name', 'category', 'feature', 'codec', 'component'],
                name='unique_subfeature'
            )
        ]

    def __str__(self):
        return self.name


class RuleGroup(models.Model):
    subfeature = models.ForeignKey(SubFeature, on_delete=models.CASCADE)
    plink = models.CharField(max_length=255, default='or')
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_rule_grops')
    updated = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(AUTH_USER_MODEL, blank=True, null=True,
                                   on_delete=models.PROTECT, related_name='updated_rule_groups')


class Rule(models.Model):
    term = models.CharField(max_length=255)
    rule_group = models.ForeignKey(RuleGroup, on_delete=models.CASCADE, related_name='rules')
