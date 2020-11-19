from dataclasses import dataclass, field
from typing import List

from django.conf import settings

from django.db import models, transaction
from django.contrib.postgres.fields import ArrayField
from django.db.models import UniqueConstraint, Q, Count
from simple_history.models import HistoricalRecords

from reporting.settings import AUTH_USER_MODEL
from .assets import *


__all__ = [
    'Generation',
    'Platform',
    'Env',
    'Component',
    'Kernel',
    'Driver',
    'Plugin',
    'Item',
    'Os',
    'OsGroup',
    'Status',
    'Run',
    'Result',
    'Validation',
    'ResultFeature'
]


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


class Kernel(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    updated_date = models.DateTimeField(max_length=40, null=True, blank=True)


class Driver(models.Model):
    name = models.CharField(max_length=255)
    build_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name', 'build_id'],
                name='unique_%(class)s_composite_constraint'
            ),
            # one null
            UniqueConstraint(
                fields=['name'], condition=Q(build_id=None),
                name='unique_%(class)s_composite_constraint_with_build_id_null'
            )
        ]

class Plugin(models.Model):
    name = models.CharField(max_length=255, unique=True)


class Item(models.Model):
    name = models.CharField(max_length=255)
    args = models.CharField(max_length=255)

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

    def __str__(self):
        return self.name


class DiffMixin(object):
    def __init__(self, *args, **kwargs):
        super(DiffMixin, self).__init__(*args, **kwargs)
        self._original_state = dict(self.__dict__)

    def get_changed_columns(self):
        missing = object()
        result = {}
        for key, value in self._original_state.items():
            if value != self.__dict__.get(key, missing):
                result[key] = value
        return result


class ResultFeature(models.Model):
    name = models.CharField(max_length=255)


class Result(DiffMixin, models.Model):
    validation = models.ForeignKey('Validation', null=True, blank=True, on_delete=models.CASCADE, related_name='results')
    driver = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, null=True, blank=True, on_delete=models.CASCADE)
    component = models.ForeignKey(Component, null=True, blank=True, on_delete=models.CASCADE)
    features = models.ManyToManyField(ResultFeature, blank=True)
    env = models.ForeignKey(Env, null=True, blank=True, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, null=True, blank=True, on_delete=models.CASCADE)
    os = models.ForeignKey(Os, null=True, blank=True, on_delete=models.CASCADE)
    kernel = models.ForeignKey(Kernel, null=True, blank=True, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, null=True, blank=True, on_delete=models.CASCADE)
    run = models.ForeignKey(Run, null=True, blank=True, on_delete=models.CASCADE)
    scenario_asset = models.ForeignKey(ScenarioAsset, null=True, blank=True, on_delete=models.CASCADE)
    msdk_asset = models.ForeignKey(MsdkAsset, null=True, blank=True, on_delete=models.CASCADE)
    os_asset = models.ForeignKey(OsAsset, null=True, blank=True, on_delete=models.CASCADE)
    lucas_asset = models.ForeignKey(LucasAsset, null=True, blank=True, on_delete=models.CASCADE)
    fulsim_asset = models.ForeignKey(FulsimAsset, null=True, blank=True, on_delete=models.CASCADE)
    simics = models.ForeignKey(Simics, null=True, blank=True, on_delete=models.CASCADE)
    additional_parameters = models.JSONField(null=True, blank=True)
    test_error = models.CharField(null=True, blank=True, max_length=1024)

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
    _changed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        skip_stats_update = kwargs.pop('skip_stats_update', False)

        if self.pk is not None and not skip_stats_update:
            # if it is not the first save
            # and statuses should be updated
            val = self.validation
            cols = self.get_changed_columns()
            if 'status_id' in cols:
                old_value = cols['status_id']
                old_status = Status.objects.get(pk=old_value).test_status
                new_status = self.status.test_status

                if new_status != old_status:
                    with transaction.atomic():
                        results_with_old_status = val.get_by_status(old_status)
                        results_with_new_status = val.get_by_status(new_status)
                        results_with_old_status -= 1
                        results_with_new_status += 1
                        val.set_by_status(old_status, results_with_old_status)
                        val.set_by_status(new_status, results_with_new_status)
                        val.save()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        val = self.validation
        status = self.status.test_status

        with transaction.atomic():
            results_with_status = val.get_by_status(status)
            results_with_status -= 1
            val.set_by_status(status, results_with_status)
            val.save()

    def similar(self, other):
        if not isinstance(other, Result):
            # don't attempt to compare against unrelated types
            return NotImplemented
        fields = ['status_id', 'scenario_asset_id', 'msdk_asset_id', 'os_asset_id', 'lucas_asset_id','fulsim_asset_id', 'simics_id', 'additional_parameters']
        for field in fields:
            if getattr(self, field, None) != getattr(other, field, None):
                return False
        return True


@dataclass
class ValidationStats:
    Passed: int = 0
    Failed: int = 0
    Error: int = 0
    Blocked: int = 0
    Skipped: int = 0
    Canceled: int = 0

    def __format__(self, spec):
        res = []
        for field in ['Passed', 'Failed', 'Error', 'Blocked', 'Skipped', 'Canceled']:
            count = getattr(self, field)
            if not count:
                continue
            if spec == 'full':
                res.append(f'{field.lower()}:{count}')
            else:
                res.append(f'{field[0].lower()}:{count}')
        return ', '.join(res)


@dataclass
class ComponentsAndFeatures:
    components: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)

    def components_as_str(self) -> str:
        if self.components:
            components = ', '.join(self.components)
        else:
            components = '<none>'

        return components

    def features_as_str(self) -> str:
        if self.features:
            features = ', '.join(self.features)
        else:
            features = '<none>'

        return features

    def __str__(self):
        components = self.components_as_str()
        features = self.features_as_str()

        return f'components: {components}; features: {features}'

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
    owner = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='validations')

    class SubSystems(models.IntegerChoices):
        VALib = 1, 'valib'

        DX9 = 9, 'DirectX 9'
        DX11 = 11, 'DirectX 11'

        __empty__ = '(Unknown)'

    subsystem = models.IntegerField(
        choices=SubSystems.choices,
        null=True
    )

    # details about Results in this validations
    passed = models.PositiveSmallIntegerField(default=0)
    failed = models.PositiveSmallIntegerField(default=0)
    error = models.PositiveSmallIntegerField(default=0)
    blocked = models.PositiveSmallIntegerField(default=0)
    skipped = models.PositiveSmallIntegerField(default=0)
    canceled = models.PositiveSmallIntegerField(default=0)

    components = ArrayField(models.IntegerField(), default=list)
    features = ArrayField(models.IntegerField(), default=list)

    def get_by_status(self, status: str) -> int:
        return getattr(self, status.lower())

    def set_by_status(self, status: str, value: int) -> None:
        setattr(self, status.lower(), value)

    def update_status_counters(self) -> ValidationStats:
        vstats = ValidationStats()
        stats = self.results.values('status').annotate(count=Count('status'))
        with transaction.atomic():
            for stat in stats:
                # status in query result is pk of Status obj
                status = Status.objects.get(pk=stat['status']).test_status
                count = stat['count']
                setattr(vstats, status, count)
                self.set_by_status(status, count)

            self.save()

        return vstats

    def update_components_and_features(self) -> ComponentsAndFeatures:
        c_and_f = ComponentsAndFeatures()

        with transaction.atomic():
            self.components = []
            for comp in self.results.values_list('component_id', 'component__name', named=True).distinct():
                c_and_f.components.append(comp.component__name)
                self.components.append(comp.component_id)

            self.features = []
            for feature in self.results.values_list('features', 'features__name', named=True).distinct():
                if feature.features is None:
                    continue
                c_and_f.features.append(feature.features__name)
                self.features.append(feature.features)

            self.save()
        return c_and_f

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['name', 'env', 'platform', 'os'],
                name='unique_%(class)s_composite_constraint'
            ),
        ]

    def __str__(self):
        return self.name

