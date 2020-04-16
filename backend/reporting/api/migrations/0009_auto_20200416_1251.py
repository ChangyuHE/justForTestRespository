# Generated by Django 3.0.4 on 2020-04-16 12:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_auto_20200413_1249'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='result',
            name='group',
        ),
        migrations.AddField(
            model_name='item',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='api.ResultGroupNew'),
        ),
        migrations.AlterField(
            model_name='resultgroupmask',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_query_name='group_mask', to='api.ResultGroupNew'),
        ),
    ]
