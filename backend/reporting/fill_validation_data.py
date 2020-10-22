import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reporting.settings")
django.setup()

from api.models import Validation

for val in Validation.objects.all():
    print(val.name)
    vstats = val.update_status_counters()
    print(f'  {vstats:full}')
    val.save()