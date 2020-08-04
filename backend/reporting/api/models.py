from pathlib import Path

from django.conf import settings

from django.db import models
from django.db.models import UniqueConstraint
from django.contrib.postgres.fields import JSONField
from django.contrib.auth import get_user_model

from reporting.settings import AUTH_USER_MODEL


class Asset(models.Model):
    root = models.CharField(max_length=255, null=True, blank=True)
    path = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    version = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True
        unique_together = ('root', 'path', 'name', 'version')

    def __str__(self):
        if self.root is None or self.path is None or self.name is None or self.version is None:
            return ''
        path = self.path if self.path.endswith('/') else f'{self.path}/'
        root = self.root if self.root.endswith('/') else f'{self.root}/'
        return f'{root}{path}{self.name}/{self.version}'


class ScenarioAsset(Asset):
    pass


class MsdkAsset(Asset):
    pass


class OsAsset(Asset):
    pass


class LucasAsset(Asset):
    pass


class FulsimAsset(Asset):
    pass


class Simics(models.Model):
    data = JSONField()


class Generation(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    weight = models.IntegerField()

    def __str__(self):
        return self.name


class Platform(models.Model):
    name = models.CharField(max_length=32)
    generation = models.ForeignKey(Generation, null=True, blank=True, on_delete=models.CASCADE, related_name='gen')
    aliases = models.CharField(max_length=255, null=True, blank=True)
    short_name = models.CharField(max_length=16, null=True, blank=True)
    weight = models.IntegerField(default=0, null=True, blank=True)
    planning = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Env(models.Model):
    name = models.CharField(max_length=32)
    short_name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Component(models.Model):
    name = models.CharField(max_length=255)


class Driver(models.Model):
    name = models.CharField(max_length=255)
    build_id = models.CharField(max_length=16, null=True, blank=True)


class Item(models.Model):
    name = models.CharField(max_length=255)
    args = models.CharField(max_length=255)
    group = models.ForeignKey('ResultGroupNew', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name', 'args'],
                name='unique_%(class)s_composite_constraint'
            ),
        ]


class Os(models.Model):
    name = models.CharField(max_length=32)
    group = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    aliases = models.CharField(max_length=255, null=True, blank=True)
    planning = models.BooleanField(default=False)
    weight = models.IntegerField(null=True, blank=True)
    shortcut = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name'],
                name='unique_os_name'
            ),
            UniqueConstraint(
                fields=['shortcut'],
                name='unique_os_shortcut'
            )
        ]

    def __str__(self):
        return self.name


class OsGroup(models.Model):
    name = models.CharField(max_length=32)
    aliases = models.CharField(max_length=255)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name'],
                name='unique_os_group_name'
            )
        ]


class Status(models.Model):
    test_status = models.CharField(max_length=255)
    priority = models.IntegerField(default=0)


class Run(models.Model):
    name = models.CharField(max_length=255)
    session = models.CharField(max_length=255)
    validation_cycle = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name', 'session'],
                name='unique_%(class)s_composite_constraint'
            ),
        ]


class Result(models.Model):
    validation = models.ForeignKey('Validation', null=True, blank=True, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, null=True, blank=True, on_delete=models.CASCADE)
    component = models.ForeignKey(Component, null=True, blank=True, on_delete=models.CASCADE)
    env = models.ForeignKey(Env, null=True, blank=True, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, null=True, blank=True, on_delete=models.CASCADE)
    os = models.ForeignKey(Os, null=True, blank=True, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, null=True, blank=True, on_delete=models.CASCADE)
    run = models.ForeignKey(Run, null=True, blank=True, on_delete=models.CASCADE)
    scenario_asset = models.ForeignKey(ScenarioAsset, null=True, blank=True, on_delete=models.CASCADE)
    msdk_asset = models.ForeignKey(MsdkAsset, null=True, blank=True, on_delete=models.CASCADE)
    os_asset = models.ForeignKey(OsAsset, null=True, blank=True, on_delete=models.CASCADE)
    lucas_asset = models.ForeignKey(LucasAsset, null=True, blank=True, on_delete=models.CASCADE)
    fulsim_asset = models.ForeignKey(FulsimAsset, null=True, blank=True, on_delete=models.CASCADE)
    simics = models.ForeignKey(Simics, null=True, blank=True, on_delete=models.CASCADE)

    exec_start = models.DateTimeField(null=True, blank=True)
    exec_end = models.DateTimeField(null=True, blank=True)

    result_key = models.CharField(max_length=255)
    result_url = models.CharField(max_length=255)
    is_best = models.BooleanField(default=False)
    is_first = models.BooleanField(default=False)
    is_last = models.BooleanField(default=False)
    is_worst = models.BooleanField(default=False)

    result_reason = models.TextField(null=True, blank=True)


class ResultGroup(models.Model):
    name = models.CharField(max_length=255)
    mask = models.CharField(max_length=255, null=True, blank=True)
    alt_name = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)


class ResultGroupNew(models.Model):
    name = models.CharField(max_length=255)
    alt_name = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Result Group'
        verbose_name_plural = 'Result Groups'


class ResultGroupMask(models.Model):
    group = models.ForeignKey(ResultGroupNew, on_delete=models.CASCADE, related_query_name='group_mask')
    mask = models.CharField(max_length=255)


class Validation(models.Model):
    name = models.CharField(max_length=255)
    env = models.ForeignKey(Env, null=True, blank=True, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, null=True, blank=True, on_delete=models.CASCADE)
    os = models.ForeignKey(Os, null=True, blank=True, on_delete=models.CASCADE)

    notes = models.TextField(null=True, blank=True)
    source_file = models.TextField(null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)

    ignore = models.BooleanField(default=False)
    hash_last = models.CharField(max_length=40, null=True, blank=True)

    class SubSystems(models.IntegerChoices):
        VALib = 1, 'valib'

        DX9 = 9, 'DirectX 9'
        DX11 = 11, 'DirectX 11'

        __empty__ = '(Unknown)'

    subsystem = models.IntegerField(
        choices=SubSystems.choices,
        null=True
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name', 'env', 'platform', 'os'],
                name='unique_%(class)s_composite_constraint'
            ),
        ]


class Action(models.Model):  # working functional, example: best, last, compare reports
    name = models.CharField(max_length=255, default='compare')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name'],
                name='unique_action_name'
            )
        ]


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
    mapping = models.ForeignKey('FeatureMapping', null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['milestone', 'feature', 'scenario', 'mapping'],
                name='unique_%(class)s_composite_constraint'
            )
        ]


class FeatureMapping(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

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


class ImportJob(models.Model):
    def xlsx() -> str:
        root = Path(settings.MEDIA_ROOT)
        return str(root / 'xlsx')

    class Status(models.TextChoices):
        PENDING = 'pending'
        FAILED = 'failed'
        DONE = 'done'
    status = models.CharField(
        max_length=7,
        choices=Status.choices,
        default=Status.PENDING
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    requester = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    path = models.FilePathField(path=xlsx)
