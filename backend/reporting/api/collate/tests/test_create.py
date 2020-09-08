import logging
import json

from django.test import Client
from django.test import TestCase
from django.urls import reverse

from api.models import Item, Os, Plugin, TestScenario
from api.utils.caches import queryset_cache

log = logging.getLogger(__name__)


class CreateEntitiesIntegrationTest(TestCase):
    def setUp(self):
        queryset_cache.clear()
        Os.objects.create(pk=23, name='Mock Os')
        self.plugin = Plugin.objects.create(name='test_plugin')
        self.scenario = TestScenario.objects.create(name='scenario_name.csv')
        print()

    def test_valid_create(self):
        client = Client()
        request = dict(entities=[
            dict(model='Os', fields={'name': 'Doors'}),
            dict(model='Os', fields={'name': 'Walls', 'group': 23}),
            dict(model='Env', fields={'name': 'Mock Env', 'short_name': 'MK'}),
            dict(model='Driver', fields={'name': 'Mock Driver'}),
            dict(model='Component', fields={'name': 'Mock Component'}),
            dict(model='Item', fields={'name': 'Mock Item name', 'args': 'Mock Item args'}),
            dict(model='Run', fields={'name': 'Mock Run name', 'session': 'Mock Run session'}),
        ])
        response = client.post(reverse('collate:create'), json.dumps(request), 'application/json')
        self.assertEqual(response.status_code, 201, 'Expected HTTP 201 Created.')

    def test_duplicate_create(self):
        client = Client()
        request = dict(entities=[
            dict(model='Os', fields={'name': 'Mock Os'}),
        ])
        response = client.post(reverse('collate:create'), json.dumps(request), 'application/json')
        self.assertEqual(response.status_code, 400, 'Expected HTTP 400 Bad request.')

    def test_invalid_group(self):
        client = Client()
        request = dict(entities=[
            dict(model='Os', fields={'name': 'Walls', 'group': 42}),
        ])
        response = client.post(reverse('collate:create'), json.dumps(request), 'application/json')
        self.assertEqual(response.status_code, 400, 'Expected HTTP 400 Bad request.')

    def test_no_entities(self):
        client = Client()
        response = client.post(reverse('collate:create'), '{}', 'application/json')
        self.assertEqual(response.status_code, 400, 'Expected HTTP 400 Bad request.')

    def test_entities_not_list(self):
        client = Client()
        response = client.post(reverse('collate:create'), '{"entities": {}}', 'application/json')
        self.assertEqual(response.status_code, 400, 'Expected HTTP 400 Bad request.')

    def test_missing_model(self):
        client = Client()
        request = dict(entities=[
            dict(name='Missing model')
        ])
        response = client.post(reverse('collate:create'), json.dumps(request), 'application/json')
        self.assertEqual(response.status_code, 400, 'Expected HTTP 400 Bad request.')

    def test_none_model(self):
        client = Client()
        request = dict(entities=[
            dict(model=None, name='Null model')
        ])
        response = client.post(reverse('collate:create'), json.dumps(request), 'application/json')
        self.assertEqual(response.status_code, 400, 'Expected HTTP 400 Bad request.')

    def test_missing_fields(self):
        client = Client()
        request = dict(entities=[
            dict(model='Os', name='Missing fields')
        ])
        response = client.post(reverse('collate:create'), json.dumps(request), 'application/json')
        self.assertEqual(response.status_code, 400, 'Expected HTTP 400 Bad request.')

    def test_none_fields(self):
        client = Client()
        request = dict(entities=[
            dict(model='Os', name='Null fields', fields=None)
        ])
        response = client.post(reverse('collate:create'), json.dumps(request), 'application/json')
        self.assertEqual(response.status_code, 400, 'Expected HTTP 400 Bad request.')

    def test_unknown_model(self):
        client = Client()
        request = dict(entities=[
            dict(model='FooBar', name='Unknown model', fields={'name': 'Foo Bar'})
        ])
        response = client.post(reverse('collate:create'), json.dumps(request), 'application/json')
        self.assertEqual(response.status_code, 400, 'Expected HTTP 400 Bad request.')

    def test_malformed_data(self):
        client = Client()
        request = dict(entities=[
            dict(model='Status', name='Missing mandatory fields',
                 fields={'test_status': 'Incorrect data', 'priority': 'malformed'})
        ])
        response = client.post(reverse('collate:create'), json.dumps(request), 'application/json')
        self.assertEqual(response.status_code, 400, 'Expected HTTP 400 Bad request.')

    def test_item_create(self):
        client = Client()
        request = dict(entities=[
            dict(model='Item', fields={'name': 'item_name', 'args': 'test_plugin foo bar -t 0001 -s scenario_name.csv'})
        ])
        response = client.post(reverse('collate:create'), json.dumps(request), 'application/json')
        self.assertEqual(response.status_code, 201, 'Expected HTTP 201 Created.')

        item = Item.objects.filter(name='item_name', args='test_plugin foo bar -t 0001 -s scenario_name.csv',
                                   plugin=self.plugin, scenario=self.scenario, test_id='0001').count()
        self.assertEqual(item, 1, 'Item not created')
