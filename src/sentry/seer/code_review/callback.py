from __future__ import annotations

import logging
from datetime import datetime

from sentry.models.code_review_event import CodeReviewEvent, CodeReviewEventStatus

logger = logging.getLogger(__name__)


def report_code_review_result(
    *,
    github_delivery_id: str,
    seer_run_id: str,
    status: str,
    comments_posted: int,
    error_message: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> dict:
    """
    Called by Seer after completing (or failing) a code review.
    Updates the corresponding CodeReviewEvent record matched by github_delivery_id.
    """
    event_record = CodeReviewEvent.objects.filter(
        github_delivery_id=github_delivery_id,
    ).first()

    if event_record is None:
        logger.warning(
            "seer.code_review.callback.no_matching_event",
            extra={
                "github_delivery_id": github_delivery_id,
                "seer_run_id": seer_run_id,
            },
        )
        return {"status": "not_found"}

    # Parse timestamps
    review_started_at = None
    if started_at:
        try:
            review_started_at = datetime.fromisoformat(started_at)
        except (ValueError, TypeError):
            pass

    review_completed_at = None
    if completed_at:
        try:
            review_completed_at = datetime.fromisoformat(completed_at)
        except (ValueError, TypeError):
            pass

    # Map Seer status to our pipeline status
    if status == "completed":
        new_status = CodeReviewEventStatus.REVIEW_COMPLETED
    elif status == "failed":
        new_status = CodeReviewEventStatus.REVIEW_FAILED
    elif status == "started":
        new_status = CodeReviewEventStatus.REVIEW_STARTED
    else:
        new_status = CodeReviewEventStatus.REVIEW_COMPLETED

    # Build update fields
    update_fields = {
        "status": new_status,
        "seer_run_id": seer_run_id,
        "comments_posted": comments_posted,
    }

    if review_started_at:
        update_fields["review_started_at"] = review_started_at
    if review_completed_at:
        update_fields["review_completed_at"] = review_completed_at
    if error_message:
        update_fields["review_result"] = {"error_message": error_message}

    CodeReviewEvent.objects.filter(id=event_record.id).update(**update_fields)

    return {"status": "ok"}
