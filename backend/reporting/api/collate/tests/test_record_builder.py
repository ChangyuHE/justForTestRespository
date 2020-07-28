from django.test import TestCase

from api.models import Platform
from api.collate.services import queryset_cache
from api.collate.services import RecordBuilder
from api.collate.services import OutcomeBuilder

platform_stub = [{
        'name': 'Arctic_Sound',
        'aliases': 'Arctic Sound;ArcticSound;',
    }, {
        'name': 'Tiger_Lake.LP',
        'aliases': 'Tiger Lake LP;',
    }, {
        'name': 'Ice_Lake_LP.U',
    }, {
        'name': 'Apollo_Lake',
        'aliases': 'Apollo Lake;ApolloLake;',
    }, {
        'name': 'DG1',
    }, {
        'name': 'Elkhard_Lake',
        'aliases': 'Elkhard Lake;elkhard_lake;elkhart_lake;',
}]

class RecordBuilderTest(TestCase):
    def setUp(self):
        queryset_cache.clear()

        for params in platform_stub:
            Platform.objects.create(**params)

    def test_find_object(self):
        name = 'DG1'

        outcome = OutcomeBuilder()
        builder = RecordBuilder(None, None, dict(), outcome)
        result = builder._find_object(Platform, name=name)

        self.assertIsNotNone(result, f'Expected {name} record.')
        self.assertTrue(type(result) == Platform, 'Expected Platform instance.')
        self.assertEqual(result.name, name, f"Expected '{name}' in name field")

    def test_find_object_ignore_case(self):
        name = 'DG1'

        outcome = OutcomeBuilder()
        builder = RecordBuilder(None, None, dict(), outcome)
        result = builder._find_object(Platform, name=name.lower())

        self.assertIsNotNone(result, f'Expected {name} record.')
        self.assertTrue(type(result) == Platform, 'Expected Platform instance.')
        self.assertEqual(result.name, name, f"Expected '{name}' in name field")

    def test_find_with_existing_alias(self):
        alias = 'ApolloLake'
        name = 'Apollo_Lake'

        outcome = OutcomeBuilder()
        builder = RecordBuilder(None, None, dict(), outcome)
        result = builder._find_with_alias(Platform, alias)

        self.assertIsNotNone(result, f'Expected {name} record.')
        self.assertEqual(result.name, name, f"Expected '{name}' in name field")

    def test_find_with_alias_ignore_case(self):
        alias = 'elkhard_lake'
        name = 'Elkhard_Lake'

        outcome = OutcomeBuilder()
        builder = RecordBuilder(None, None, dict(), outcome)
        result = builder._find_with_alias(Platform, alias)

        self.assertIsNotNone(result, f'Expected {name} record.')
        self.assertEqual(result.name, name, f"Expected '{name}' in name field")

    def test_find_with_alias_by_name(self):
        name = 'Tiger_Lake.LP'

        outcome = OutcomeBuilder()
        builder = RecordBuilder(None, None, dict(), outcome)
        result = builder._find_with_alias(Platform, name)

        self.assertIsNotNone(result, f'Expected {name} record.')
        self.assertEqual(result.name, name, f"Expected '{name}' in name field")

    def test_find_with_alias_by_name_ignore_case(self):
        name = 'Tiger_Lake.LP'

        outcome = OutcomeBuilder()
        builder = RecordBuilder(None, None, dict(), outcome)
        result = builder._find_with_alias(Platform, name.lower())

        self.assertIsNotNone(result, f'Expected {name} record.')
        self.assertEqual(result.name, name, f"Expected '{name}' in name field")

    def test_find_with_alias_part(self):
        name = 'lake'

        outcome = OutcomeBuilder()
        builder = RecordBuilder(None, None, dict(), outcome)
        result = builder._find_with_alias(Platform, name)

        self.assertIsNone(result, f'Expected empty record instead of {result}.')

