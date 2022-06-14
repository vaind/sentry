import os
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional

from django.conf import settings


class ProfileKey(Enum):
    RELEASE_HEALTH = "release-health"
    PERFORMANCE = "performance"


DEFAULT_PROFILE_KEY = ProfileKey.RELEASE_HEALTH


@dataclass(frozen=True)
class MetricsIngestConfiguration:
    db_model: ProfileKey
    input_topic: str
    output_topic: str
    use_case_id: Optional[str]
    internal_metrics_tag: Optional[str]


_METRICS_INGEST_CONFIG: Mapping[ProfileKey, MetricsIngestConfiguration] = {
    ProfileKey.RELEASE_HEALTH: MetricsIngestConfiguration(
        db_model=ProfileKey.RELEASE_HEALTH,
        input_topic=settings.KAFKA_INGEST_METRICS,
        output_topic=settings.KAFKA_SNUBA_METRICS,
        # For non-SaaS deploys one may want a different use_case_id here
        # This keeps our internal schema consistent with the launch
        # of performance metrics
        use_case_id=None,
        internal_metrics_tag="release-health",
    ),
    ProfileKey.PERFORMANCE: MetricsIngestConfiguration(
        db_model=ProfileKey.PERFORMANCE,
        input_topic=settings.KAFKA_INGEST_PERFORMANCE_METRICS,
        output_topic=settings.KAFKA_SNUBA_GENERIC_METRICS,
        use_case_id="performance",
        internal_metrics_tag="perf",
    ),
}


def get_ingest_config(
    environment_key: str = "SENTRY_METRICS_INGEST_PROFILE",
) -> MetricsIngestConfiguration:
    env_value = os.environ.get(environment_key)
    return _METRICS_INGEST_CONFIG[ProfileKey(env_value) if env_value else DEFAULT_PROFILE_KEY]
