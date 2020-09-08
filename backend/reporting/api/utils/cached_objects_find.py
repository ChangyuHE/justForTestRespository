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
    'plugin': {'class': Plugin, 'pattern': re.compile(r'^(test_\w+)')},
    'scenario': {'class': TestScenario, 'pattern': re.compile(r'-s (\S+)')},
    'test_id': {'class': None, 'pattern': re.compile(r'-[it] (\S+)')},
}


def parse_item_args(params) -> Tuple[dict, dict]:
    # remove leading, trailing and consecutive spaces
    params['args'] = ' '.join(params['args'].strip().split())

    full_params = {**params}
    non_existing = {}

    for name, extra in TEST_ITEM_EXTRAS.items():
        m = extra['pattern'].search(params['args'])
        matched = m.group(1) if m else None

        if extra['class'] is not None:
            # trying to find object by name using match
            if matched is not None:
                found_object = find_object(cls=extra['class'], name=matched)
                if found_object:
                    full_params[f'{name}_id'] = found_object.id
                else:
                    # add key value pair to create later
                    non_existing[name] = matched
            else:
                full_params[f'{name}_id'] = None
        else:
            full_params[name] = matched

    return full_params, non_existing
