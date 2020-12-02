from django.test import Client
from django.urls import reverse

from api.models import MergeJob
from api.models import Result
from api.models import Validation
from .db_fixture import DramatiqFixture

class MergeValidationsIntegrationTest(DramatiqFixture):
    job_model = MergeJob
    fixtures = ['collate/test_merge_fixture.json']

    def setUp(self):
        super().setUp()
        self.request = dict(
            validation_ids=[],
            validation_name='Test merge api',
            notes='Notes',
        )

    def test_empty_validation_list(self):
        client = Client()
        response = client.post(reverse('collate:merge'), self.request)
        self.assertContains(response, 'ERR_VALIDATION_LIST', status_code=422)

    def test_missing_validation_list(self):
        del(self.request['validation_ids'])

        client = Client()
        response = client.post(reverse('collate:merge'), self.request)
        self.assertContains(response, 'ERR_VALIDATION_LIST', status_code=422)

    def test_empty_validation_name(self):
        self.request['validation_name'] = ''

        client = Client()
        response = client.post(reverse('collate:merge'), self.request)
        self.assertContains(response, 'ERR_EMPTY_VALIDATION_NAME', status_code=422)

    def test_missing_validation_name(self):
        del(self.request['validation_name'])

        client = Client()
        response = client.post(reverse('collate:merge'), self.request)
        self.assertContains(response, 'ERR_EMPTY_VALIDATION_NAME', status_code=422)

    def test_existing_validation(self):
        self.request['validation_name'] = 'Validation 2019ww29'
        self.request['validation_ids'] = [27, 30]

        client = Client()
        response = client.post(reverse('collate:merge'), self.request)
        self.assertContains(response, 'ERR_EXISTING_VALIDATION', status_code=422)

    def test_compatible_validations(self):
        self.request['validation_ids'] = [27, 30]

        client = Client()
        response = client.post(reverse('collate:merge'), self.request)
        self.assertImportSuccess(response.data)

    def test_incompatible_validations(self):
        self.request['validation_ids'] = [27, 136]

        client = Client()
        response = client.post(reverse('collate:merge'), self.request)
        self.assertContains(response, 'ERR_AMBIGUOUS_COLUMN', status_code=422)

    def test_merge_best(self):
        self.request['validation_ids'] = [27, 30, 34]
        self.request['strategy'] = 'best'

        client = Client()
        response = client.post(reverse('collate:merge'), self.request)
        self.assertImportSuccess(response.data)

        new_validation_id = Validation.alive_objects.last().pk

        merged_result_values = Result.objects.filter(
                validation_id=new_validation_id
            ).values_list('status__priority', flat=True)

        expected_len = 1
        actual_len = len(merged_result_values)
        self.assertEqual(expected_len, actual_len)

        expected_priority = 50
        actual_priority = merged_result_values[0]
        self.assertEqual(expected_priority, actual_priority)

    def test_merge_last(self):
        self.request['validation_ids'] = [27, 30, 34]
        self.request['strategy'] = 'last'

        client = Client()
        response = client.post(reverse('collate:merge'), self.request)
        self.assertImportSuccess(response.data)

        new_validation_id = Validation.objects.last().pk

        merged_result_values = Result.objects.filter(
                validation_id=new_validation_id
            ).values_list('status__priority', flat=True)

        expected_len = 1
        actual_len = len(merged_result_values)
        self.assertEqual(expected_len, actual_len)

        expected_priority = 20
        actual_priority = merged_result_values[0]
        self.assertEqual(expected_priority, actual_priority)
