from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sentry.models.code_review_event import CodeReviewEvent, CodeReviewEventStatus

logger = logging.getLogger(__name__)

SEER_STATUS_MAP: dict[str, CodeReviewEventStatus] = {
    "completed": CodeReviewEventStatus.REVIEW_COMPLETED,
    "failed": CodeReviewEventStatus.REVIEW_FAILED,
    "started": CodeReviewEventStatus.REVIEW_STARTED,
}


def _parse_timestamp(value: str | None) -> datetime | None:
    """Parse an ISO timestamp string, returning None on invalid input."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def report_code_review_result(
    *,
    trigger_id: str,
    seer_run_id: str,
    status: str,
    comments_posted: int,
    error_message: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> dict:
    """
    Called by Seer after completing (or failing) a code review.
    Updates the corresponding CodeReviewEvent record matched by trigger_id.
    """
    event_record = CodeReviewEvent.objects.filter(
        trigger_id=trigger_id,
    ).first()

    if event_record is None:
        logger.warning(
            "seer.code_review.callback.no_matching_event",
            extra={
                "trigger_id": trigger_id,
                "seer_run_id": seer_run_id,
            },
        )
        return {"status": "not_found"}

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

    return {"status": "ok"}
