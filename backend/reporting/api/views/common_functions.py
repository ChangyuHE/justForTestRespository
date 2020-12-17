from typing import Optional, List

from sqlalchemy.orm import Query

from api.models import Feature, FeatureMapping, FeatureMappingRule
from test_verifier.models import Codec


def fmt_rules(fmt_pks: Optional[List[int]]=None) -> Query:
    return FeatureMappingRule.sa \
        .query(FeatureMappingRule.sa.scenario_id, Feature.sa.name.label('Feature'),
               Codec.sa.name.label('Codec')) \
        .select_from(FeatureMappingRule.sa) \
        .filter(FeatureMappingRule.sa.mapping_id.in_(fmt_pks)) \
        .join(FeatureMapping.sa) \
        .join(Feature.sa) \
        .join(Codec.sa)
