from django.db import models


class Action(models.Model):  # working functional, example: best, last, compare reports
    name = models.CharField(max_length=255, default='compare', unique=True)
