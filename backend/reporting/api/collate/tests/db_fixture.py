import logging

from io import BytesIO
from unittest.mock import patch

from django_dramatiq.test import DramatiqTestCase
from django.contrib.auth.models import User

from api.models import Component, Driver, Env, ImportJob, Item, Os, Platform, Plugin, Run, Status, TestScenario, \
    Validation

from api.collate.gta_field_parser import GTAFieldParser
from api.utils.caches import queryset_cache

from api.collate.tests.genetated_files import create_file
from api.collate.tests.genetated_files import create_empty_workbook

log = logging.getLogger(__name__)


class DbFixture(DramatiqTestCase):
    def setUp(self):
        queryset_cache.clear()

        self.request = dict(
            validation_id=42,
            validation_name='Test model',
            notes='Notes',
        )

        env = Env.objects.create(name='Silicon')
        platform = Platform.objects.create(name='DG1')
        os = Os.objects.create(name='Windows 19H1 x64', aliases='Windows')
        Os.objects.create(name='Linux')
        Run.objects.create(name='Test run', session='Test session')
        self.auth_user = User.objects.create_user(username='debug', password='12345')

        Validation.objects.create(pk=42, name='Test model', env=env, platform=platform, os=os, owner=self.auth_user)

        Driver.objects.create(name='gfx-driver-ci-master-3172')
        Component.objects.create(name='Media-Encode')

        plugin = Plugin.objects.create(name='test_media_lucas')
        scenario = TestScenario.objects.create(name='KBL_VDEnc_TEDDI_ISPFormats_CQP.csv')
        Item.objects.create(name='Lucas - Media Encode - VDEnc TEDDI ISPFormats CQP_135',
                            args='test_media_lucas -s KBL_VDEnc_TEDDI_ISPFormats_CQP.csv -t 135',
                            plugin=plugin, scenario=scenario, test_id='135')
        Item.objects.create(name='Lucas - Media Encode - VDEnc TEDDI ISPFormats CQP_123',
                            args='test_media_lucas -s KBL_VDEnc_TEDDI_ISPFormats_CQP.csv -t 123',
                            plugin=plugin, scenario=scenario, test_id='123')
        Item.objects.create(name='Lucas - Media Encode - VDEnc TEDDI ISPFormats CQP_112',
                            args='test_media_lucas -s KBL_VDEnc_TEDDI_ISPFormats_CQP.csv -t 112',
                            plugin=plugin, scenario=scenario, test_id='112')
        scenario = TestScenario.objects.create(name='KBL_AVC_VDEnc_TEDDI_MultiRef_CQP_Unified.csv')
        Item.objects.create(name='Lucas - Media Encode - VDEnc TEDDI MultiRef CQP -KBL_115',
                            args='test_media_lucas -s KBL_AVC_VDEnc_TEDDI_MultiRef_CQP_Unified.csv -t 115',
                            plugin=plugin, scenario=scenario, test_id='115')
        scenario = TestScenario.objects.create(name='KBL_AVC_VDEnc_TEDDI_VBR_MultiRef_MBBRC_Unified.csv')
        Item.objects.create(name='Lucas - Media Encode - VDEnc TEDDI MultiRef BRC_KBL_105',
                            args='test_media_lucas -s KBL_AVC_VDEnc_TEDDI_VBR_MultiRef_MBBRC_Unified.csv -t 105',
                            plugin=plugin, scenario=scenario, test_id='105')

        Status.objects.create(test_status='Failed', priority=100)
        Status.objects.create(test_status='Passed', priority=100)

        gta_patcher = patch.object(GTAFieldParser, 'fetch_from')
        gta_patcher.start()
        self.addCleanup(gta_patcher.stop)

    def tearDown(self):
        self.join_dramatiq_worker()

    def join_dramatiq_worker(self):
        self.broker.join('default')
        self.worker.join()

    def assertImportSuccess(self, response_data):
        self.join_dramatiq_worker()

        job_id = response_data.get('job_id', None)
        self.assertIsNotNone(job_id)

        job = ImportJob.objects.get(pk=job_id)
        self.assertEqual(job.status, ImportJob.Status.DONE)

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
