# Generated by Django 3.1.1 on 2020-09-09 16:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_add_testid_plugin_scenario_to_item'),
    ]

    operations = [
        migrations.AlterField(
            model_name='result',
            name='additional_parameters',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='simics',
            name='data',
            field=models.JSONField(),
        ),
    ]
