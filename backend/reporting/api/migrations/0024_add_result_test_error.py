# Generated by Django 3.1.1 on 2020-11-11 09:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0023_fix_kernel_name_and_add_related_name_to_validation_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalresult',
            name='test_error',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='test_error',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
