"""
Handle GitHub check_run webhook events for PR review rerun.
When a user clicks "Re-run" on a check run in GitHub UI, we enqueue
a task to forward the original run ID to Seer.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ValidationError

from sentry.integrations.github.webhook_types import GithubWebhookType

from ..event_recorder import update_event_status
from ..metrics import (
    CodeReviewErrorType,
    WebhookFilteredReason,
    record_webhook_enqueued,
    record_webhook_filtered,
    record_webhook_handler_error,
    record_webhook_received,
)

logger = logging.getLogger(__name__)


class Log(StrEnum):
    MISSING_ACTION = "github.webhook.check_run.missing-action"
    INVALID_PAYLOAD = "github.webhook.check_run.invalid-payload"


class GitHubCheckRunAction(StrEnum):
    COMPLETED = "completed"
    CREATED = "created"
    REQUESTED_ACTION = "requested_action"
    REREQUESTED = "rerequested"


class GitHubCheckRunData(BaseModel):
    """GitHub check_run object structure."""

    external_id: str
    html_url: str

    class Config:
        extra = "allow"


class GitHubCheckRunEvent(BaseModel):
    """
    GitHub check_run webhook event payload.
    https://docs.github.com/en/webhooks/webhook-events-and-payloads#check_run
    """

    action: str
    check_run: GitHubCheckRunData

    class Config:
        extra = "allow"


def handle_check_run_event(
    *,
    github_event: GithubWebhookType,
    event: Mapping[str, Any],
    extra: Mapping[str, str | None],
    event_record: Any | None = None,
    **kwargs: Any,
) -> None:
    if github_event != GithubWebhookType.CHECK_RUN:
        return

    action = event.get("action")

    if action is None:
        logger.error(Log.MISSING_ACTION.value, extra=extra)
        record_webhook_handler_error(
            github_event,
            action or "",
            CodeReviewErrorType.MISSING_ACTION,
        )
        return

    record_webhook_received(github_event, action)

    if action != GitHubCheckRunAction.REREQUESTED:
        record_webhook_filtered(github_event, action, WebhookFilteredReason.UNSUPPORTED_ACTION)
        update_event_status(event_record, "webhook_filtered", denial_reason="unsupported_action")
        return

    try:
        validated_event = _validate_github_check_run_event(event)
    except (ValidationError, ValueError):
        logger.exception(Log.INVALID_PAYLOAD.value, extra=extra)
        record_webhook_handler_error(
            github_event,
            action,
            CodeReviewErrorType.INVALID_PAYLOAD,
        )
        return

    from .task import process_github_webhook_event

    trigger_id = getattr(event_record, "trigger_id", None) if event_record else None

    process_github_webhook_event.delay(
        github_event=github_event.value,
        event_payload={"original_run_id": validated_event.check_run.external_id},
        action=validated_event.action,
        html_url=validated_event.check_run.html_url,
        enqueued_at_str=datetime.now(timezone.utc).isoformat(),
        trigger_id=trigger_id,
    )
    record_webhook_enqueued(github_event, action)
    update_event_status(event_record, "task_enqueued")


def _validate_github_check_run_event(event: Mapping[str, Any]) -> GitHubCheckRunEvent:
    """Raises ValidationError or ValueError if the payload is invalid."""
    validated_event = GitHubCheckRunEvent.parse_obj(event)
    int(validated_event.check_run.external_id)  # Must be numeric
    return validated_event
