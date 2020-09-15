from django.test import TestCase

from api.models import FeatureMapping
from api.view.feature_mapping import check_mappings


class FeatureMappingMatchTest(TestCase):
    fixtures = [
        '../tests/fixtures/users.json', 'Codec.json', 'component.json', 'driver.json', 'env.json', 'generation.json',
        'item.json', 'os.json', 'platform.json', 'resultgroupmask.json', 'resultgroupnew.json', 'run.json', 'status.json',
        'milestone.json', 'plugin.json', 'testscenario.json', 'feature.json', 'featuremapping.json', 'featuremappingrule.json',
        'simics.json', 'scenario_asset.json', 'os_asset.json', 'msdk_asset.json', 'lucas_asset.json', 'fulsim_asset.json',
        '../tests/fixtures/results.json', '../tests/fixtures/validations.json'
    ]

    def test_codec_conflicts(self):
        names = ['AVCe mapping', 'mpeg2e mapping', 'some linux mapping', 'HEVCd mapping', 'AVCe draft']
        # duplicate AVCe codec
        mapping_ids = FeatureMapping.objects.filter(name__in=names).values_list('id', flat=True)
        self.assertFalse(check_mappings(mapping_ids), 'Mappings with one codec not allowed')

        # no duplicates
        mapping_ids = FeatureMapping.objects.filter(name__in=names[:-1]).values_list('id', flat=True)
        self.assertTrue(check_mappings(mapping_ids), 'Mappings with different codecs allowed')

        # different oses
        mapping_ids = FeatureMapping.objects.filter(name__in=['some linux mapping', 'HEVCd mapping']) \
            .values_list('id', flat=True)
        self.assertTrue(check_mappings(mapping_ids), 'Mappings with different codecs and oses allowed')
