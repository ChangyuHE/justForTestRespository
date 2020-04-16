import re
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reporting.settings")
django.setup()

from api.models import *

# rg_queryset = ResultGroup.objects.filter(mask__isnull=False).\
#     annotate(mask_fixed=Func(F('mask'), Value('.'), Value(r'\.'), function='replace')).\
#     annotate(mask_fixed=Func(F('mask_fixed'), Value('*'), Value(r'.*?'), function='replace'))\
#     .order_by('id')

unknown_group = ResultGroupNew.objects.get(name='Unknown')

items = Item.objects.all().order_by('id')
for i in items:
    for mask, group_id in ResultGroupNew.objects.all().values_list('group_mask__mask', 'id'):
        if mask is None:
            continue

        m = re.search(mask, i.name)
        if m:
            i.group_id = group_id
            break
    else:
        i.group_id = unknown_group.id

Item.objects.bulk_update(items, ['group'], batch_size=100)
