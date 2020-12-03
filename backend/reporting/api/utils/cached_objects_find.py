import re
from typing import Tuple

from api.models import Item, Plugin, TestScenario
from .caches import queryset_cache


# Objects finding methods
def find_object(cls, **params):
    for obj in queryset_cache.get(cls):
        if __match_by_params(obj, params):
            return obj
    return None


def find_testitem_object(**params):
    extended_params, non_existing = parse_item_args(params)
    if not non_existing:
        for obj in queryset_cache.get(Item):
            if __match_by_params(obj, extended_params):
                queryset_cache.clear(Item)
                return obj
    queryset_cache.clear(Item)
    return None


def find_with_alias(cls, alias):
    if alias is None:
        return None

    for obj in queryset_cache.get(cls):
        if __match_by_alias(obj, alias):
            return obj
    return None


def __match_by_params(obj, params):
    found = True

    for key, value in params.items():
        # case insensitive strings compare
        if type(value) != str:
            found &= getattr(obj, key) == value
        else:
            attr = getattr(obj, key, None)

            if attr is not None:
                found &= attr.lower() == value.lower()
            else:
                found = False
                break

    return found


def __match_by_alias(obj, name):
    ignore_case_name = name.lower()

    if obj.name.lower() == ignore_case_name:
        return True

    if obj.aliases is None:
        return False

    if ignore_case_name in __iterate_aliases(obj.aliases):
        return True

    return False


def __iterate_aliases(aliases):
    return (x for x in map(str.strip, aliases.lower().split(';')) if x)


TEST_ITEM_EXTRAS = {
    'plugin': {'class': Plugin, 'patterns': [re.compile(r'^(test_\w+)')]},
    'scenario': {
        'class': TestScenario,
        'patterns': [re.compile(r'-s (\S+)'), re.compile(r'test_hlk\s.*/name:([^#\s]+).*')]
    }
}


def parse_item_args(params) -> Tuple[dict, dict]:
    # remove leading, trailing and consecutive spaces
    params['args'] = ' '.join(params['args'].strip().split())

    full_params = {**params}
    non_existing = {}

    if m := re.search(r'-[it] (\S+)', params['args']):
        full_params['test_id'] = m[1]

    for name, extra in TEST_ITEM_EXTRAS.items():
        name_id = f'{name}_id'

        for pattern in extra['patterns']:
            m = pattern.search(params['args'])

            if not m:
                # do not null if found in previous pattern
                if full_params.get(name_id) is None:
                    full_params[name_id] = None
            else:
                # trying to find object by name using match
                obj = find_object(cls=extra['class'], name=m[1])
                if obj:
                    full_params[name_id] = obj.id
                else:
                    # add key value pair to create later
                    non_existing[name] = m[1]

    return full_params, non_existing
