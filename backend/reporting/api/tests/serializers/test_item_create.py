from django.test import TestCase

from api.models import Plugin, TestScenario
from api.serializers import ItemSerializer
from . import cases


class CreateTestItemTest(TestCase):
    def setUp(self):
        Plugin.objects.create(name='test_msdk')
        TestScenario.objects.create(name='scenario_name')
        self.serializer_class = ItemSerializer

    def test_existing_relations(self):
        for data, expected in cases.EXISTING_RELATIONS:
            with self.subTest(data=data):
                serializer = self.serializer_class(data=data)
                self.assertEqual(serializer.is_valid(), True)
                self.assertDictEqual(serializer.validated_data, expected)

    def test_new_relations(self):
        for data, expected in cases.NEW_RELATIONS:
            with self.subTest(data=data):
                serializer = self.serializer_class(data=data)
                self.assertEqual(serializer.is_valid(), True)
                self.assertDictEqual(serializer.validated_data, expected)
