from django.db import models


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
