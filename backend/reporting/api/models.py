from pathlib import Path

from django.conf import settings

from django.db import models
from django.db.models import UniqueConstraint, Q
from simple_history.models import HistoricalRecords

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
    data = models.JSONField()

    def __str__(self):
        return str(self.data)


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

    def __str__(self):
        return self.name


class Driver(models.Model):
    name = models.CharField(max_length=255)
    build_id = models.CharField(max_length=16, null=True, blank=True)

    def __str__(self):
        return self.name


class Plugin(models.Model):
    name = models.CharField(max_length=255, unique=True)


class Item(models.Model):
    name = models.CharField(max_length=255)
    args = models.CharField(max_length=255)
    group = models.ForeignKey('ResultGroupNew', null=True, blank=True, on_delete=models.SET_NULL)

    plugin = models.ForeignKey(Plugin, null=True, blank=True, on_delete=models.CASCADE)
    scenario = models.ForeignKey('TestScenario', null=True, blank=True, on_delete=models.CASCADE)
    test_id = models.CharField(null=True, blank=True, max_length=255)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name', 'args', 'plugin', 'scenario', 'test_id'],
                name='unique_%(class)s_composite_constraint'
            ),
            # all nulls
            UniqueConstraint(
                fields=['name', 'args'], condition=Q(test_id=None) & Q(scenario=None) & Q(plugin=None),
                name='unique_%(class)s_composite_constraint_with_all_nulls'
            ),
            # two nulls
            UniqueConstraint(
                fields=['name', 'args', 'plugin'], condition=Q(scenario=None) & Q(test_id=None),
                name='unique_%(class)s_composite_constraint_with_scen_id_nulls'
            ),
            UniqueConstraint(
                fields=['name', 'args', 'scenario'], condition=Q(plugin=None) & Q(test_id=None),
                name='unique_%(class)s_composite_constraint_with_plugin_id_nulls'
            ),
            UniqueConstraint(
                fields=['name', 'args', 'test_id'], condition=Q(plugin=None) & Q(scenario=None),
                name='unique_%(class)s_composite_constraint_with_plugin_scen_nulls'
            ),
            # one null
            UniqueConstraint(
                fields=['name', 'args', 'plugin', 'scenario'], condition=Q(test_id=None),
                name='unique_%(class)s_composite_constraint_with_id_null'
            ),
            UniqueConstraint(
                fields=['name', 'args', 'plugin', 'test_id'], condition=Q(scenario=None),
                name='unique_%(class)s_composite_constraint_with_scen_null'
            ),
            UniqueConstraint(
                fields=['name', 'args', 'scenario', 'test_id'], condition=Q(plugin=None),
                name='unique_%(class)s_composite_constraint_with_plugin_null'
            )
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
        verbose_name_plural = 'Oses'

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

    class Meta:
        verbose_name_plural = 'Statuses'

    def __str__(self):
        return self.test_status


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
    additional_parameters = models.JSONField(null=True, blank=True)

    exec_start = models.DateTimeField(null=True, blank=True)
    exec_end = models.DateTimeField(null=True, blank=True)

    result_key = models.CharField(max_length=255)
    result_url = models.CharField(max_length=255)
    is_best = models.BooleanField(default=False)
    is_first = models.BooleanField(default=False)
    is_last = models.BooleanField(default=False)
    is_worst = models.BooleanField(default=False)

    result_reason = models.TextField(null=True, blank=True)
    history = HistoricalRecords()


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
    env = models.ForeignKey(Env, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    os = models.ForeignKey(Os, on_delete=models.CASCADE)

    notes = models.TextField(null=True, blank=True)
    source_file = models.TextField(null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)

    ignore = models.BooleanField(default=False)
    hash_last = models.CharField(max_length=40, null=True, blank=True)
    owner = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.PROTECT)

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

    def __str__(self):
        return self.name


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
    ids = models.TextField(null=True, blank=True)

    mapping = models.ForeignKey('FeatureMapping', null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
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


def xlsx() -> str:
    root = Path(settings.MEDIA_ROOT)
    return str(root / 'xlsx')


class ImportJob(models.Model):
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
    requester = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.PROTECT)
    path = models.FilePathField(path=xlsx)
    force_run = models.BooleanField(default=False)
    force_item = models.BooleanField(default=False)
    site_url = models.CharField(max_length=255)
