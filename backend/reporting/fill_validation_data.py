import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reporting.settings")
django.setup()

from api.models import Validation

for val in Validation.objects.all():
    print(val.name)
    vstats = val.update_status_counters()
    comp_and_feat = val.update_components_and_features()
    print(f'  {vstats:full}')
    print(f'  {comp_and_feat}')
    val.save()