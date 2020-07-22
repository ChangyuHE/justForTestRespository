from django.db import models
from django.db.models import UniqueConstraint

from api.models import Platform


class Codec(models.Model):
    name = models.CharField(max_length=255, unique=True)


class FeatureCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)


class Feature(models.Model):
    name = models.CharField(max_length=255, unique=True)


class SubFeature(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(FeatureCategory, null=True, blank=True, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, null=True, blank=True, on_delete=models.CASCADE)
    codec = models.ForeignKey(Codec, null=True, blank=True, on_delete=models.CASCADE)
    lin_platforms = models.ManyToManyField(Platform, related_name='lin_subfeatures')
    win_platforms = models.ManyToManyField(Platform, related_name='win_subfeatures')
    notes = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name', 'category', 'feature', 'codec'],
                name='unique_subfeature'
            )
        ]
