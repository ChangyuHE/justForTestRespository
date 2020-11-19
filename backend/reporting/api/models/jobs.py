from pathlib import Path

from django.db import models
from django.conf import settings

from reporting.settings import AUTH_USER_MODEL


def xlsx() -> str:
    root = Path(settings.MEDIA_ROOT)
    return str(root / 'xlsx')


class JobStatus(models.TextChoices):
    PENDING = 'pending'
    FAILED = 'failed'
    DONE = 'done'


class ImportJob(models.Model):
    status = models.CharField(
        max_length=7,
        choices=JobStatus.choices,
        default=JobStatus.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    requester = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.PROTECT)
    path = models.FilePathField(path=xlsx)
    force_run = models.BooleanField(default=False)
    force_item = models.BooleanField(default=False)
    site_url = models.CharField(max_length=255)


class MergeJob(models.Model):
    status = models.CharField(
        max_length=7,
        choices=JobStatus.choices,
        default=JobStatus.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    requester = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.PROTECT)
    validation_name = models.CharField(max_length=255)
    notes = models.TextField(null=True, blank=True)
    site_url = models.CharField(max_length=255)
    strategy = models.CharField(max_length=255)


class CloneJob(models.Model):
    status = models.CharField(
        max_length=7,
        choices=JobStatus.choices,
        default=JobStatus.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    requester = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.PROTECT)
    validation_name = models.CharField(max_length=255)
    notes = models.TextField(null=True, blank=True)
    site_url = models.CharField(max_length=255)
