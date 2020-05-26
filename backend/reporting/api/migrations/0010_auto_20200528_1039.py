# Generated by Django 3.0.4 on 2020-05-28 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_auto_20200416_1251'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='validation',
            constraint=models.UniqueConstraint(fields=('name', 'env', 'platform', 'os'), name='unique_validation_composite_constraint'),
        ),
    ]
