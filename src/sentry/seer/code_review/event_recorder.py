"""
Helper functions for creating and updating CodeReviewEvent records.
These track the lifecycle of each webhook event through the code review pipeline.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from sentry.models.code_review_event import CodeReviewEvent, CodeReviewEventStatus

logger = logging.getLogger(__name__)


def _extract_pr_metadata(
    github_event_type: str,
    event: Mapping[str, Any],
) -> dict[str, Any]:
    """Extract PR metadata from a webhook payload based on event type."""
    pr_number = None
    pr_title = None
    pr_author = None
    pr_url = None

    if github_event_type == "pull_request":
        pr = event.get("pull_request", {})
        pr_number = pr.get("number")
        pr_title = pr.get("title")
        pr_author = pr.get("user", {}).get("login")
        pr_url = pr.get("html_url")
    elif github_event_type == "issue_comment":
        issue = event.get("issue", {})
        pr_number = issue.get("number")
        pr_title = issue.get("title")
        pr_author = issue.get("user", {}).get("login")
        pr_url = issue.get("pull_request", {}).get("html_url")

    return {
        "pr_number": pr_number,
        "pr_title": pr_title,
        "pr_author": pr_author,
        "pr_url": pr_url,
    }


def create_event_record(
    *,
    organization_id: int,
    repository_id: int,
    github_event_type: str,
    github_event_action: str,
    github_delivery_id: str | None,
    event: Mapping[str, Any],
    status: str,
    denial_reason: str | None = None,
) -> CodeReviewEvent | None:
    """Create a CodeReviewEvent record. Returns None if creation fails."""
    now = datetime.now(timezone.utc)
    pr_metadata = _extract_pr_metadata(github_event_type, event)

    timestamp_field = _status_to_timestamp_field(status)
    timestamps = {timestamp_field: now} if timestamp_field else {}

    try:
        return CodeReviewEvent.objects.create(
            organization_id=organization_id,
            repository_id=repository_id,
            github_event_type=github_event_type,
            github_event_action=github_event_action,
            github_delivery_id=github_delivery_id,
            status=status,
            denial_reason=denial_reason,
            **pr_metadata,
            **timestamps,
        )
    except Exception:
        logger.exception(
            "seer.code_review.event_recorder.create_failed",
            extra={
                "organization_id": organization_id,
                "repository_id": repository_id,
                "github_delivery_id": github_delivery_id,
            },
        )
        return None


def update_event_status(
    event_record: CodeReviewEvent | None,
    status: str,
    *,
    denial_reason: str | None = None,
) -> None:
    """Update the status of an existing CodeReviewEvent record."""
    if event_record is None:
        return

    now = datetime.now(timezone.utc)
    update_fields: dict[str, Any] = {"status": status}

    if denial_reason:
        update_fields["denial_reason"] = denial_reason

    timestamp_field = _status_to_timestamp_field(status)
    if timestamp_field:
        update_fields[timestamp_field] = now

    try:
        CodeReviewEvent.objects.filter(id=event_record.id).update(**update_fields)
    except Exception:
        logger.exception(
            "seer.code_review.event_recorder.update_failed",
            extra={
                "event_record_id": event_record.id,
                "status": status,
            },
        )


def find_event_by_delivery_id(github_delivery_id: str) -> CodeReviewEvent | None:
    """Find a CodeReviewEvent by github_delivery_id."""
    if not github_delivery_id:
        return None
    return CodeReviewEvent.objects.filter(github_delivery_id=github_delivery_id).first()


def _status_to_timestamp_field(status: str) -> str | None:
    """Map a status to its corresponding timestamp field."""
    return {
        CodeReviewEventStatus.WEBHOOK_RECEIVED: "webhook_received_at",
        CodeReviewEventStatus.PREFLIGHT_DENIED: "preflight_completed_at",
        CodeReviewEventStatus.WEBHOOK_FILTERED: "preflight_completed_at",
        CodeReviewEventStatus.TASK_ENQUEUED: "task_enqueued_at",
        CodeReviewEventStatus.SENT_TO_SEER: "sent_to_seer_at",
        CodeReviewEventStatus.REVIEW_STARTED: "review_started_at",
        CodeReviewEventStatus.REVIEW_COMPLETED: "review_completed_at",
        CodeReviewEventStatus.REVIEW_FAILED: "review_completed_at",
    }.get(status)
