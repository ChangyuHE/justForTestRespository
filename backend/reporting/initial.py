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
    # 'Driver': 'PUBLIC_DRIVERS.json',
    # 'Env': 'PUBLIC_ENV.json',
    # 'Component': 'PUBLIC_COMPONENTS.json',
    # 'Generation': 'PUBLIC_GENERATIONS.json',
    # 'Platform': 'PUBLIC_PLATFORMS.json',
    # 'Item': 'PUBLIC_ITEMS.json',
    # 'Os': 'PUBLIC_OS.json',
    # 'Status': 'PUBLIC_STATUSES.json',
    # 'Run': 'PUBLIC_TESTRUNS.json',
    # 'Result': 'PUBLIC_RESULTS.json',
    # 'Validation': 'PUBLIC_VALIDATIONS.json',
    'ResultGroup': 'PUBLIC_RESULTGROUPS.json'

}

for model_name, json_file in files_mapping.items():
    data = []
    print(model_name)
    klass = globals()[model_name]
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

