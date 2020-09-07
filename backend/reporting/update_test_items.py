import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reporting.settings")
django.setup()

from api.models import Item, Result
from api.utils.cached_objects_find import parse_item_args, TEST_ITEM_EXTRAS


for item in Item.objects.all().order_by('id'):
    to_save = False
    params, non_existing = parse_item_args(dict(name=item.name, args=item.args))

    if item.args != params['args']:
        item.args = params['args']
        to_save = True

    for field in ('plugin', 'scenario', 'test'):
        value = params.get(f'{field}_id')
        if value is not None and getattr(item, f'{field}_id') != value:
            setattr(item, f'{field}_id', value)
            to_save = True

    for field, value in non_existing.items():
        model_class = TEST_ITEM_EXTRAS[field]['class']
        relation_object, _ = model_class.objects.get_or_create(name=value)
        setattr(item, f'{field}_id', relation_object.id)
        to_save = True

    if to_save:
        try:
            item.save()
        except django.db.utils.IntegrityError as e:
            if 'duplicate key value violates unique constraint' in str(e):
                # get item id with right params
                right_item_id = Item.objects.get(
                    name=item.name, args=item.args, plugin=item.plugin, scenario=item.scenario, test_id=item.test_id
                ).id
                # update existing results for our item with right item id
                for result in Result.objects.filter(item_id=item.id):
                    result.item_id = right_item_id
                    result.save()
            else:
                raise
