import logging

from io import BytesIO
from django.urls import reverse
from django.test import Client

from api.models import Result
from api.models import Validation
from api.models import Os
from api.models import Platform
from api.models import Env
from .db_fixture import DbFixture


log = logging.getLogger(__name__)


class ImportFileIntegrationTest(DbFixture):
    def test_no_file(self):
        client = Client()
        response = client.post(reverse('collate:import'), self.request)
        self.assertEqual(response.status_code, 400,
                         f'Expected HTTP 400 Bad request, actual {response.status_code} {response.data}')

    def test_invalid_file(self):
        self.set_file(BytesIO(b''))
        client = Client()
        response = client.post(reverse('collate:import'), self.request)
        self.assertContains(response, 'ERR_WORKBOOK_EXCEPTION', status_code=422)

    def test_existing_validation_id(self):
        self.set_file('import_existing_validation.json')
        self.request.pop('validation_name')
        client = Client()
        response = client.post(reverse('collate:import'), self.request)

        expected_count = 1
        actual_count = Validation.objects.count()
        self.assertEqual(response.status_code, 200,
                         f'Expected HTTP 200 Ok, actual {response.status_code} {response.data}')
        self.assertEqual(expected_count, actual_count,
                         f'Expected {expected_count} Validation records, but actual is {actual_count}')

    def test_nonexisting_validation_id(self):
        self.set_file('import_existing_validation.json')
        self.request['validation_id'] = 73
        client = Client()
        response = client.post(reverse('collate:import'), self.request)
        self.assertContains(response, 'ERR_INVALID_VALIDATION_ID', status_code=422)

    def test_existing_validation_create(self):
        self.set_file('import_existing_validation.json')
        self.request.pop('validation_id')
        client = Client()
        response = client.post(reverse('collate:import'), self.request)
        self.assertContains(response, 'ERR_EXISTING_VALIDATION', status_code=422)

    def test_nonexisting_validation_create(self):
        self.set_file('import_existing_validation.json')
        self.request.pop('validation_id')
        self.request['validation_name'] = 'New validation'
        client = Client()
        response = client.post(reverse('collate:import'), self.request)

        expected_count = 2
        actual_count = Validation.objects.count()
        self.assertEqual(response.status_code, 200,
                         f'Expected HTTP 200 Ok, actual {response.status_code} {response.data}')
        self.assertEqual(expected_count, actual_count,
                         f'Expected {expected_count} Validation records, but actual is {actual_count}')

    def test_invalid_validation_id(self):
        self.set_file('import_err_invalid_validation.json')
        self.request['validation_id'] = 73
        client = Client()
        response = client.post(reverse('collate:import'), self.request)
        self.assertContains(response, 'ERR_INVALID_VALIDATION_ID', status_code=422)

    def test_empty_content(self):
        self.set_empty_file()
        self.request.pop('validation_id')
        client = Client()
        response = client.post(reverse('collate:import'), self.request)
        self.assertContains(response, 'ERR_WORKBOOK_EXCEPTION', status_code=422)

    def test_valid_file(self):
        self.set_file('import_ok.json')
        client = Client()
        response = client.post(reverse('collate:import'), self.request)
        self.assertEqual(response.status_code, 200,
                         f'Expected HTTP 200, actual {response.status_code} {response.data}')
        self.assertEquals(response.data.get('success', None), True,
                          f'Expected import success, actual {response.status_code} {response.data}')

    def test_missing_columns(self):
        self.set_file('import_err_missing_columns.json')
        client = Client()
        response = client.post(reverse('collate:import'), self.request)
        self.assertContains(response, 'ERR_MISSING_COLUMNS', status_code=422)

    def test_missing_values(self):
        self.set_file('import_err_missing_values.json')
        client = Client()
        response = client.post(reverse('collate:import'), self.request)
        self.assertContains(response, 'ERR_MISSING_ENTITY', status_code=422)

    def test_ambiguous_values(self):
        Os.objects.create(name='Doors', aliases='Doors; Walls; Floors;')
        Platform.objects.create(name='Concrete')
        Env.objects.create(name='Wednesday')

        self.set_file('import_err_ambiguous_values.json')
        client = Client()
        response = client.post(reverse('collate:import'), self.request)
        self.assertContains(response, 'ERR_AMBIGUOUS_COLUMN', status_code=422)

    def test_create_validation(self):
        self.set_file('import_err_create_validation.json')
        self.request.pop('validation_id')
        self.request['validation_name'] = 'New validation'

        client = Client()
        response = client.post(reverse('collate:import'), self.request)

        self.assertContains(response, 'ERR_MISSING_ENTITY', status_code=422)
        self.assertContains(response, 'ERR_AMBIGUOUS_COLUMN', status_code=422)
        self.assertContains(response, 'ERR_EXISTING_RUN', status_code=422)


class ImportDatetimeParserTest(DbFixture):
    def test_invalid_date(self):
        self.set_file('import_err_invalid_date.json')
        client = Client()
        response = client.post(reverse('collate:import'), self.request)
        self.assertContains(response, 'invalid-date-value', status_code=422)

    def test_empty_date(self):
        self.set_file('import_err_empty_date.json')
        client = Client()
        response = client.post(reverse('collate:import'), self.request)
        self.assertEqual(response.status_code, 200,
                         f'Expected HTTP 200, actual {response.status_code} {response.data}')

    def test_date_conversion(self):
        self.set_file('import_ok_date_conversion.json')
        client = Client()
        response = client.post(reverse('collate:import'), self.request)
        self.assertEqual(response.status_code, 200,
                         f'Expected HTTP 200, actual {response.status_code} {response.data}')
