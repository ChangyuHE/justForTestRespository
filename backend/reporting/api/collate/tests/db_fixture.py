from io import BytesIO

from django.test import TestCase

from api.models import Component
from api.models import Driver
from api.models import Env
from api.models import Item
from api.models import Os
from api.models import Platform
from api.models import Run
from api.models import Status
from api.models import Validation

from api.collate.tests.genetated_files import create_file
from api.collate.tests.genetated_files import create_empty_workbook


class DbFixture(TestCase):
    def setUp(self):
        self.request = dict(
            validation_id=42,
            validation_name='Test model',
            notes='Notes',
        )

        env = Env.objects.create(name='Silicon')
        platform = Platform.objects.create(name='DG1')
        os = Os.objects.create(name='Windows')
        Os.objects.create(name='Linux')
        Run.objects.create(name='Test run', session='Test session')

        Validation.objects.create(pk=42, name='Test model', env=env, platform=platform, os=os)

        Driver.objects.create(name='gfx-driver-ci-master-3172')
        Component.objects.create(name='Media-Encode')

        Item.objects.create(name='Lucas - Media Encode - VDEnc TEDDI ISPFormats CQP_135',
                args='test_media_lucas -s KBL_VDEnc_TEDDI_ISPFormats_CQP.csv -t 135')
        Item.objects.create(name='Lucas - Media Encode - VDEnc TEDDI MultiRef CQP -KBL_115',
                args='test_media_lucas -s KBL_AVC_VDEnc_TEDDI_MultiRef_CQP_Unified.csv -t 115')
        Item.objects.create(name='Lucas - Media Encode - VDEnc TEDDI MultiRef BRC_KBL_105',
                args='test_media_lucas -s KBL_AVC_VDEnc_TEDDI_VBR_MultiRef_MBBRC_Unified.csv -t 105')
        Item.objects.create(name='Lucas - Media Encode - VDEnc TEDDI ISPFormats CQP_123',
                args='test_media_lucas -s KBL_VDEnc_TEDDI_ISPFormats_CQP.csv -t 123')
        Item.objects.create(name='Lucas - Media Encode - VDEnc TEDDI ISPFormats CQP_112',
                args='test_media_lucas -s KBL_VDEnc_TEDDI_ISPFormats_CQP.csv -t 112')

        Status.objects.create(test_status='Failed', priority=100)
        Status.objects.create(test_status='Passed', priority=100)

        print()

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
