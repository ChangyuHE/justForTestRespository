from django.db import models


class Generation(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    weight = models.IntegerField()


class Platform(models.Model):
    name = models.CharField(max_length=32)
    generation = models.ForeignKey(Generation, null=True, blank=True, on_delete=models.CASCADE, related_name='gen')
    aliases = models.CharField(max_length=255, null=True, blank=True)
    short_name = models.CharField(max_length=16, null=True, blank=True)
    weight = models.IntegerField(default=0, null=True, blank=True)
    planning = models.BooleanField(default=False)


class Env(models.Model):
    name = models.CharField(max_length=32)
    short_name = models.CharField(max_length=10)


class Component(models.Model):
    name = models.CharField(max_length=255)


class Driver(models.Model):
    name = models.CharField(max_length=255)


class Item(models.Model):
    name = models.CharField(max_length=255)
    args = models.CharField(max_length=255)
    group = models.ForeignKey('ResultGroupNew', null=True, blank=True, on_delete=models.DO_NOTHING)


class Os(models.Model):
    name = models.CharField(max_length=32)
    group = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    aliases = models.CharField(max_length=255, null=True, blank=True)
    planning = models.BooleanField(default=False)


class Status(models.Model):
    test_status = models.CharField(max_length=255)
    priority = models.IntegerField(default=0)


class Run(models.Model):
    name = models.CharField(max_length=255)
    session = models.CharField(max_length=255)
    validation_cycle = models.CharField(max_length=255, null=True, blank=True)


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


class ResultGroupMask(models.Model):
    group = models.ForeignKey(ResultGroupNew, on_delete=models.CASCADE, related_query_name='group_mask')
    mask = models.CharField(max_length=255)


class Validation(models.Model):
    name = models.CharField(max_length=255)
    env = models.ForeignKey(Env, null=True, blank=True, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, null=True, blank=True, on_delete=models.CASCADE)
    os = models.ForeignKey(Os, null=True, blank=True, on_delete=models.CASCADE)

    class SubSystems(models.IntegerChoices):
        VALib = 1, 'valib'

        DX9 = 9, 'DirectX 9'
        DX11 = 11, 'DirectX 11'

        __empty__ = '(Unknown)'

    subsystem = models.IntegerField(
        choices=SubSystems.choices,
        null=True
    )

    notes = models.TextField(null=True, blank=True)
    source_file = models.TextField(null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)

    ignore = models.BooleanField(default=False)
    hash_last = models.CharField(max_length=40, null=True, blank=True)
