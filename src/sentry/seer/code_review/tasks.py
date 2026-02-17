from __future__ import annotations

import logging
from datetime import timedelta

from django.utils import timezone

from sentry.models.code_review_event import CodeReviewEvent
from sentry.silo.base import SiloMode
from sentry.tasks.base import instrumented_task
from sentry.taskworker.namespaces import seer_code_review_tasks

logger = logging.getLogger(__name__)

RETENTION_DAYS = 90


@instrumented_task(
    name="sentry.seer.code_review.tasks.cleanup_old_code_review_events",
    namespace=seer_code_review_tasks,
    silo_mode=SiloMode.REGION,
)
def cleanup_old_code_review_events() -> None:
    """Delete CodeReviewEvent records older than 90 days."""

    cutoff = timezone.now() - timedelta(days=RETENTION_DAYS)
    deleted_count, _ = CodeReviewEvent.objects.filter(date_added__lt=cutoff).delete()
    if deleted_count:
        logger.info(
            "seer.code_review.cleanup.completed",
            extra={"deleted_count": deleted_count, "cutoff": cutoff.isoformat()},
        )
