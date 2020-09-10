from unittest.mock import patch
from random import randint

from django.forms.models import model_to_dict

from api.models import Component
from api.models import Env
from api.models import Item
from api.models import Os
from api.models import Platform
from api.models import Result
from api.models import Run
from api.models import Status
from api.models import Validation

from api.collate import services
from api.collate.business_entities import Context
from api.collate.services import RecordBuilder

from api.collate.tests.db_fixture import DbFixture


class UpdateRecordTestCase(DbFixture):
    def setUp(self):
        super().setUp()

        self.builder = RecordBuilder(Context(), None)
        self.entity = self.__create__random_result()
        self.existing_entity = self.__create__random_result()

        patcher = patch.object(services, '_find_existing_entity')
        self.mock_find_entity = patcher.start()
        self.addCleanup(patcher.stop)

    def __create__random_result(self):
        def rnd():
            return randint(1, 1000)
        suffix = rnd()

        env = Env(name=f'Test Env {suffix}', short_name=f'TE{suffix}')
        component = Component(name=f'Test Component {suffix}')
        item = Item(name=f'Test Item {suffix}', args=f'args {suffix}')
        status = Status(test_status='Passed', priority=suffix)
        platform = Platform(name=f'Test Platform {suffix}')
        os = Os(name=f'Test Os {suffix}')
        run = Run(name=f'Test Run {suffix}', session=f'Test Session {suffix}')

        return Result(
            validation = Validation(
                name = f'Test Validation {suffix}',
                env = env,
                platform = platform,
                os = os,
            ),
            env = env,
            platform = platform,
            os = os,
            component = component,
            item = item,
            status = status,
            run = run,
        )

    def assertEntityEqual(self, expected, actual):
        expected_dict = model_to_dict(expected)
        actual_dict = model_to_dict(actual)

        for item in [expected_dict, actual_dict]:
            del(item['id'])

        self.assertDictEqual(expected_dict, actual_dict)

    def test_entity_does_not_exist(self):
        self.mock_find_entity.return_value = None

        actual_entity = self.builder._RecordBuilder__update_if_exists(self.entity)
        self.assertEqual(self.entity, actual_entity)

    def test_existing_entity(self):
        self.mock_find_entity.return_value = self.existing_entity

        actual_entity = self.builder._RecordBuilder__update_if_exists(self.entity)
        self.assertEntityEqual(self.entity, actual_entity)
        self.assertEqual(self.existing_entity, actual_entity)
        self.assertNotEqual(self.existing_entity, self.entity)
