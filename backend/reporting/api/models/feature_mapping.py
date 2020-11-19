from django.db import models
from django.db.models import UniqueConstraint, Q

from reporting.settings import AUTH_USER_MODEL
from .validation import Os, Platform, Component


class Milestone(models.Model):
    name = models.CharField(max_length=255, unique=True)


class Feature(models.Model):
    name = models.CharField(max_length=255, unique=True)


class TestScenario(models.Model):
    name = models.CharField(max_length=255, unique=True)


class FeatureMappingRule(models.Model):
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    scenario = models.ForeignKey(TestScenario, on_delete=models.CASCADE)
    ids = models.TextField(null=True, blank=True)
    total = models.PositiveIntegerField(null=True, blank=True, default=None)

    mapping = models.ForeignKey('FeatureMapping', related_name='rules', null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ['milestone__name']
        constraints = [
            UniqueConstraint(
                fields=['milestone', 'feature', 'scenario', 'mapping', 'ids'],
                name='unique_%(class)s_composite_constraint_with_ids'
            ),
            UniqueConstraint(
                fields=['milestone', 'feature', 'scenario', 'mapping'],
                condition=Q(ids=None),
                name='unique_%(class)s_composite_constraint_without_ids'
            )
        ]


class FeatureMapping(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.PROTECT)

    codec = models.ForeignKey('test_verifier.Codec', on_delete=models.CASCADE)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    os = models.ForeignKey(Os, on_delete=models.CASCADE)

    public = models.BooleanField(default=False)
    official = models.BooleanField(default=False)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name', 'owner'],
                name='unique_%(class)s_composite_constraint'
            )
        ]
