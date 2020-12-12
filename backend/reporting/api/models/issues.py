from django.db import models
from bulk_update_or_create import BulkUpdateOrCreateQuerySet


class Issue(models.Model):
    class Exposure(models.IntegerChoices):
        Showstopper = 4
        High = 3
        Medium = 2
        Low = 1
        Undecided = 0

    objects = BulkUpdateOrCreateQuerySet.as_manager()
    name = models.CharField(max_length=50, primary_key=True)
    self_url = models.CharField(max_length=255, null=True)
    summary = models.CharField(max_length=255)
    description = models.TextField(null=True)
    status = models.CharField(max_length=255, null=True)
    updated = models.DateTimeField(null=True)
    product = models.CharField(max_length=255, null=True)
    closed_reason = models.CharField(max_length=255, null=True)
    root_cause = models.TextField(null=True, blank=True)
    oses = models.JSONField()
    exposure = models.PositiveSmallIntegerField(default=0, choices=Exposure.choices)
    components = models.JSONField()
    platforms = models.JSONField()

    def __str__(self):
        return f'[{self.name}] {self.summary}'
