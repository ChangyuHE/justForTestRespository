# Generated by Django 3.0.4 on 2020-08-28 13:26

import api.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

from utils.api_helpers import get_default_owner


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0009_feature_mapping_codec_and_ids'),
    ]

    operations = [
        migrations.AddField(
            model_name='validation',
            name='owner',
            field=models.ForeignKey(default=get_default_owner, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='validation',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='importjob',
            name='path',
            field=models.FilePathField(path=api.models.xlsx),
        ),
        migrations.AlterField(
            model_name='validation',
            name='env',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Env'),
        ),
        migrations.AlterField(
            model_name='validation',
            name='os',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Os'),
        ),
        migrations.AlterField(
            model_name='validation',
            name='platform',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Platform'),
        ),
    ]
