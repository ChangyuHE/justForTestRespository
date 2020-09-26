import logging

from io import BytesIO
from unittest.mock import patch

from django_dramatiq.test import DramatiqTestCase
from django.test import TransactionTestCase

from api.models import ImportJob
from api.models import JobStatus
from api.collate.gta_field_parser import GTAFieldParser
from api.utils.caches import queryset_cache

from api.collate.tests.genetated_files import create_file
from api.collate.tests.genetated_files import create_empty_workbook

log = logging.getLogger(__name__)


class DbFixture(TransactionTestCase):
    fixtures = ['collate/db_fixture.json']

    def setUp(self):
        queryset_cache.clear()

        self.request = dict(
            validation_id=42,
            validation_name='Test model',
            notes='Notes',
        )

        gta_patcher = patch.object(GTAFieldParser, 'fetch_from')
        gta_patcher.start()
        self.addCleanup(gta_patcher.stop)

    def set_file(self, source):
        if type(source) != str:
            self.request['file'] = source
        else:
            sample_valid_workbook = create_file(source)
            mem_file = BytesIO()
            sample_valid_workbook.save(mem_file)
            mem_file.seek(0)

            self.request['file'] = mem_file

    def set_empty_file(self):
        workbook = create_empty_workbook()
        mem_file = BytesIO()
        workbook.save(mem_file)
        mem_file.seek(0)

        self.request['file'] = mem_file


class DramatiqFixture(DramatiqTestCase, DbFixture):
    job_model = ImportJob

    def setUp(self):
        DramatiqTestCase.setUp(self)
        DbFixture.setUp(self)

    def tearDown(self):
        self.join_dramatiq_worker()
        DbFixture.tearDown(self)
        DramatiqTestCase.tearDown(self)

    def join_dramatiq_worker(self):
        self.broker.join('default')
        self.worker.join()

    def assertImportSuccess(self, response_data):
        self.join_dramatiq_worker()

        job_id = response_data.get('job_id', None)
        self.assertIsNotNone(job_id)

        job = self.job_model.objects.get(pk=job_id)
        self.assertEqual(job.status, JobStatus.DONE)
