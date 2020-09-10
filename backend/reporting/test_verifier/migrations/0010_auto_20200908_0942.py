# Generated by Django 3.0.4 on 2020-09-08 09:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('test_verifier', '0009_user_fk_on_delete'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rulegroup',
            name='subfeature',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rule_group', to='test_verifier.SubFeature'),
        ),
        migrations.AlterField(
            model_name='rulegroup',
            name='updated',
            field=models.DateTimeField(auto_now=True, null=True),
        )
    ]
