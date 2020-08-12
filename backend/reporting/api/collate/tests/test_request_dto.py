from datetime import datetime
from types import SimpleNamespace

from django.test import TestCase
from django.utils import timezone

from api.collate.business_entities import RequestDTO

class RequestDtoTest(TestCase):
    def setUp(self):
        self.request = SimpleNamespace(data={})
        self.request.build_absolute_uri = lambda x: 'test_uri'

    def test_missing_validation_id(self):
        dto = RequestDTO.build(self.request)
        self.assertIsNone(dto.validation_id)

    def test_empty_validation_id(self):
        self.request.data['validation_id'] = ''
        dto = RequestDTO.build(self.request)
        self.assertIsNone(dto.validation_id)

    def test_blank_validation_id(self):
        self.request.data['validation_id'] = ' '
        dto = RequestDTO.build(self.request)
        self.assertIsNone(dto.validation_id)

    def test_valid_validation_id(self):
        expected_id = 42

        self.request.data['validation_id'] = expected_id
        dto = RequestDTO.build(self.request)

        self.assertEqual(expected_id, dto.validation_id)

    def test_missing_date(self):
        dto = RequestDTO.build(self.request)

        time_delta = timezone.make_aware(datetime.now()) - dto.date
        absolute_delta = abs(time_delta.total_seconds())

        message = 'Expected current datetime in dto if date is missing in request.'
        self.assertLess(absolute_delta, 3, message)

    def test_empty_date(self):
        self.request.data['validation_date'] = ''
        dto = RequestDTO.build(self.request)

        time_delta = timezone.make_aware(datetime.now()) - dto.date
        absolute_delta = abs(time_delta.total_seconds())

        message = 'Expected current datetime in dto if date is empty in request.'
        self.assertLess(absolute_delta, 3, message)

    def test_blank_date(self):
        self.request.data['validation_date'] = ' '
        dto = RequestDTO.build(self.request)

        time_delta = timezone.make_aware(datetime.now()) - dto.date
        absolute_delta = abs(time_delta.total_seconds())

        message = 'Expected current datetime in dto if date is blank in request.'
        self.assertLess(absolute_delta, 3, message)

    def test_valid_date(self):
        expected_date = '2020-08-01'
        self.request.data['validation_date'] = expected_date
        dto = RequestDTO.build(self.request)

        self.assertEqual(expected_date, dto.date)

    def test_force_run_boolean(self):
        self.request.data['force_run'] = True
        dto = RequestDTO.build(self.request)

        self.assertTrue(dto.force_run)

    def test_force_run_string_boolean(self):
        self.request.data['force_run'] = 'True'
        dto = RequestDTO.build(self.request)

        self.assertTrue(dto.force_run)

    def test_force_run_string_boolean_lower(self):
        self.request.data['force_run'] = 'true'
        dto = RequestDTO.build(self.request)

        self.assertTrue(dto.force_run)

    def test_force_run_string_on(self):
        self.request.data['force_run'] = 'on'
        dto = RequestDTO.build(self.request)

        self.assertTrue(dto.force_run)

    def test_missing_force_run(self):
        dto = RequestDTO.build(self.request)
        self.assertFalse(dto.force_run)

    def test_build_uri(self):
        dto = RequestDTO.build(self.request)
        self.assertEqual(dto.site_url, 'test_uri')
