# Generated by Django 3.0.4 on 2020-06-25 11:47

from django.db import migrations


NEW_VALUES = {
    "Windows 10 RS5": 'rs5',
    "Windows 10 RS4": 'rs4',
    "Windows 10 RS2": 'rs2',
    "Windows 10 RS3": 'rs3',
    "Windows 10 RS1": 'rs1',
    "Windows 10 19H2": '19h2',
    "Windows 10 19H1": '19h1',
    "Windows 10 20H1": '20h1',
    "Ubuntu 16.04": '16.04',
    "Ubuntu 18.04": '18.04',
    "Ubuntu 19.04": '19.04',
    "CentOS": 'centos'
}


def add_shortcut(apps, schema_editor):
    Os = apps.get_model('api', 'os')
    for name, shortcut in NEW_VALUES.items():
        os = Os.objects.get(name=name)
        os.shortcut = shortcut
        os.save()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_auto_20200625_1446'),
    ]

    operations = [
        migrations.RunPython(add_shortcut)
    ]
