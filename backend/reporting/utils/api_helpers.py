from rest_framework.response import Response


def serialiazed_to_datatable_json(serialized, exclude=None, actions=True):
    """ Convert serialized data in dict format to DataTable headers and items """

    if exclude is None:
        exclude = []

    headers, items = [], []
    if not serialized:
        return {'headers': [], 'items': []}

    for field_name, field_value in serialized[0].items():
        if field_name in exclude:
            continue

        # integers (boolean as well) and string values
        if isinstance(field_value, int) or isinstance(field_value, str):
            value = field_name
        elif field_name == 'platform':
            value = 'platform.short_name'
        elif field_name == 'owner':
            value = 'owner.username'
        else:
            value = f'{field_name}.name'

        headers.append({'text': field_name.title(), 'sortable': True, 'value': value})

    if actions:
        headers.append({'text': 'Actions', 'value': 'actions', 'sortable': False, 'width': 10})

    for data in serialized:
        item_data = dict()
        for field_name, field_value in data.items():
            if field_name in exclude:
                continue

            if field_value is not None:
                item_data[field_name] = field_value
            else:
                item_data[field_name] = None

        items.append(item_data)
    return {'headers': headers, 'items': items}


def get_datatable_json(_self, actions=True, exclude=None):
    """ DRF generic API view that returns DataTable formatted json """

    queryset = _self.filter_queryset(_self.get_queryset())
    page = _self.paginate_queryset(queryset)
    if page is not None:
        serializer = _self.get_serializer(page, many=True)
        return _self.get_paginated_response(serializer.data)
    serializer = _self.get_serializer(queryset, many=True)

    return Response(serialiazed_to_datatable_json(serializer.data, actions=actions, exclude=exclude))
