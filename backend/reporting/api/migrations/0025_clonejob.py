# Generated by Django 3.1.1 on 2020-11-12 07:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0024_add_result_test_error'),
    ]

    operations = [
        migrations.CreateModel(
            name='CloneJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('failed', 'Failed'), ('done', 'Done')], default='pending', max_length=7)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('validation_name', models.CharField(max_length=255)),
                ('notes', models.TextField(blank=True, null=True)),
                ('site_url', models.CharField(max_length=255)),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
