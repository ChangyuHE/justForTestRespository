import os
import json
import django
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reporting.settings")

django.setup()

root_dir = Path('/home/webapps/json')
fixtures_dir = Path('./api/fixtures')

from api.models import *

files_mapping = {
    # 'driver': 'PUBLIC_DRIVERS.json',
    # 'env': 'PUBLIC_ENV.json',
    # 'component': 'PUBLIC_COMPONENTS.json',
    # 'generation': 'PUBLIC_GENERATIONS.json',
    # 'platform': 'PUBLIC_PLATFORMS.json',
    # 'item': 'PUBLIC_ITEMS.json',
    # 'os': 'PUBLIC_OS.json',
    # 'status': 'PUBLIC_STATUSES.json',
    # 'run': 'PUBLIC_TESTRUNS.json',
    'result': 'PUBLIC_RESULTS.json',
    'validation': 'PUBLIC_VALIDATIONS.json',

}

for model_name, json_file in files_mapping.items():
    data = []
    print(model_name)
    klass = globals()[model_name.capitalize()]
    field_names = [field.name for field in klass._meta.fields if field.name != 'id']
    print(field_names)

    with open(root_dir / json_file) as f:
        json_data = json.loads(f.read())

    for d in json_data:
        # print(d)
        u = {'pk': d['ID'], 'model': f'api.{model_name}', 'fields': {}}
        for field_name in field_names:
            u['fields'][field_name] = d[field_name]

        data.append(u)

    print(data[0])

    (fixtures_dir / f'{model_name}.json').unlink(missing_ok=True)
    (fixtures_dir / f'{model_name}.json').write_text(json.dumps(data))

