import re
import os
import django
from pathlib import Path
from django.db.models import Func, Value, F

from api.models import *

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reporting.settings")
django.setup()

# rg_queryset = ResultGroup.objects.filter(mask__isnull=False).\
#     annotate(mask_fixed=Func(F('mask'), Value('.'), Value(r'\.'), function='replace')).\
#     annotate(mask_fixed=Func(F('mask_fixed'), Value('*'), Value(r'.*?'), function='replace'))\
#     .order_by('id')

unknown_group = ResultGroupNew.objects.get(name='Unknown')

results = Result.objects.all().order_by('id').select_related('item')
for r in results:
    for mask, group_id in ResultGroupNew.objects.all().values_list('group_mask__mask', 'id'):
        if mask is None:
            continue

        m = re.search(mask, r.item.name)
        if m:
            r.group_id = group_id
            break
    else:
        r.group_id = unknown_group.id

Result.objects.bulk_update(results, ['group'], batch_size=100)
