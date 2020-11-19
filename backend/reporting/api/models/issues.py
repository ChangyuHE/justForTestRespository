from django.db import models
from bulk_update_or_create import BulkUpdateOrCreateQuerySet


class Issues(models.Model):
    objects = BulkUpdateOrCreateQuerySet.as_manager()
    name = models.CharField(max_length=50, unique=True, primary_key=True)
    self_url = models.CharField(max_length=255, null=True)
    summary = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=255, null=True)
    updated = models.DateTimeField(null=True)
    product = models.CharField(max_length=255, null=True)
    closed_reason = models.CharField(max_length=255, null=True)
    root_cause = models.TextField(null=True, blank=True)
    oses = models.JSONField()
    exposure = models.CharField(max_length=255, null=True)
    components = models.JSONField()
    platforms = models.JSONField()
