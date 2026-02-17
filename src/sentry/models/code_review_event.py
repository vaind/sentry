from __future__ import annotations

from enum import StrEnum

from django.db import models
from django.utils import timezone

from sentry.backup.scopes import RelocationScope
from sentry.db.models import (
    BoundedBigIntegerField,
    BoundedPositiveIntegerField,
    Model,
    region_silo_model,
    sane_repr,
)


class CodeReviewEventStatus(StrEnum):
    WEBHOOK_RECEIVED = "webhook_received"
    PREFLIGHT_DENIED = "preflight_denied"
    WEBHOOK_FILTERED = "webhook_filtered"
    TASK_ENQUEUED = "task_enqueued"
    SENT_TO_SEER = "sent_to_seer"
    REVIEW_STARTED = "review_started"
    REVIEW_COMPLETED = "review_completed"
    REVIEW_FAILED = "review_failed"
    PR_CLOSED_SENT = "pr_closed_sent"


@region_silo_model
class CodeReviewEvent(Model):
    """
    Records every GitHub webhook event entering the Seer code review pipeline.
    Tracks the full lifecycle from webhook receipt to review completion.
    """

    __relocation_scope__ = RelocationScope.Excluded

    organization_id = BoundedBigIntegerField(db_index=True)
    repository_id = BoundedPositiveIntegerField()

    # PR identification
    pr_number = models.IntegerField(null=True)
    pr_title = models.TextField(null=True)
    pr_author = models.TextField(null=True)
    pr_url = models.TextField(null=True)
    pr_state = models.CharField(max_length=16, null=True)  # open, closed, merged

    # Webhook event metadata
    trigger_event_type = models.CharField(max_length=64)
    trigger_event_action = models.CharField(max_length=64)
    trigger_id = models.CharField(max_length=64, null=True)

    # Provider-agnostic fields (aligns with SeerCodeReviewConfig)
    trigger = models.CharField(max_length=64, null=True)
    trigger_user = models.TextField(null=True)
    trigger_at = models.DateTimeField(null=True)

    target_commit_sha = models.CharField(max_length=64, null=True)

    # Pipeline status
    status = models.CharField(max_length=32)
    denial_reason = models.TextField(null=True)

    # Timestamps for pipeline stages
    date_added = models.DateTimeField(default=timezone.now, db_index=True)
    webhook_received_at = models.DateTimeField(null=True)
    preflight_completed_at = models.DateTimeField(null=True)
    task_enqueued_at = models.DateTimeField(null=True)
    sent_to_seer_at = models.DateTimeField(null=True)
    review_started_at = models.DateTimeField(null=True)
    review_completed_at = models.DateTimeField(null=True)

    # Seer callback data
    seer_run_id = models.CharField(max_length=64, null=True)
    comments_posted = models.IntegerField(null=True)
    review_result = models.JSONField(null=True)

    class Meta:
        app_label = "sentry"
        db_table = "sentry_code_review_event"
        indexes = (
            models.Index(fields=("organization_id", "date_added")),
            models.Index(fields=("organization_id", "repository_id", "date_added")),
            models.Index(fields=("organization_id", "status", "date_added")),
            models.Index(fields=("organization_id", "repository_id", "pr_number")),
        )
        constraints = [
            models.UniqueConstraint(
                fields=["trigger_id"],
                name="unique_trigger_id",
                condition=models.Q(trigger_id__isnull=False),
            ),
        ]

    __repr__ = sane_repr("organization_id", "repository_id", "pr_number", "status")
