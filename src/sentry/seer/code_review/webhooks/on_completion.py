from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sentry.models.code_review_event import CodeReviewEvent, CodeReviewEventStatus
from sentry.tasks.base import instrumented_task
from sentry.taskworker.namespaces import seer_tasks

logger = logging.getLogger(__name__)

SEER_STATUS_MAP: dict[str, CodeReviewEventStatus] = {
    "completed": CodeReviewEventStatus.REVIEW_COMPLETED,
    "failed": CodeReviewEventStatus.REVIEW_FAILED,
    "started": CodeReviewEventStatus.REVIEW_STARTED,
}


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


@instrumented_task(
    name="sentry.seer.code_review.webhooks.on_completion.process_pr_review_completion",
    namespace=seer_tasks,
    retry=None,
)
def process_pr_review_completion(*, payload: dict[str, Any]) -> None:
    trigger_id = payload.get("trigger_id")
    if not trigger_id:
        logger.warning(
            "seer.code_review.webhook.missing_trigger_id",
            extra={"payload_keys": list(payload.keys())},
        )
        return

    seer_run_id = payload.get("seer_run_id")
    status = payload.get("status", "completed")
    comments_posted = payload.get("comments_posted", 0)
    error_message = payload.get("error_message")
    started_at = payload.get("started_at")
    completed_at = payload.get("completed_at")

    event_record = CodeReviewEvent.objects.filter(trigger_id=trigger_id).first()

    if event_record is None:
        logger.warning(
            "seer.code_review.webhook.no_matching_event",
            extra={
                "trigger_id": trigger_id,
                "seer_run_id": seer_run_id,
            },
        )
        return

    new_status = SEER_STATUS_MAP.get(status, CodeReviewEventStatus.REVIEW_COMPLETED)

    update_fields: dict[str, Any] = {
        "status": new_status,
        "seer_run_id": seer_run_id,
        "comments_posted": comments_posted,
    }

    review_started_at = _parse_timestamp(started_at)
    if review_started_at:
        update_fields["review_started_at"] = review_started_at

    review_completed_at = _parse_timestamp(completed_at)
    if review_completed_at:
        update_fields["review_completed_at"] = review_completed_at

    if error_message:
        update_fields["review_result"] = {"error_message": error_message}

    CodeReviewEvent.objects.filter(id=event_record.id).update(**update_fields)
