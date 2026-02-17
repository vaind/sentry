from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from datetime import datetime
from typing import Any, TypedDict

from sentry.api.serializers import Serializer, register
from sentry.models.code_review_event import CodeReviewEvent
from sentry.models.repository import Repository


def _iso_or_none(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


class CodeReviewEventResponse(TypedDict):
    id: str
    organizationId: str
    repositoryId: str
    repositoryName: str | None
    prNumber: int | None
    prTitle: str | None
    prAuthor: str | None
    prUrl: str | None
    githubEventType: str
    githubEventAction: str
    githubDeliveryId: str | None
    trigger: str | None
    triggerUser: str | None
    triggerAt: str | None
    targetCommitSha: str | None
    status: str
    denialReason: str | None
    dateAdded: str
    webhookReceivedAt: str | None
    preflightCompletedAt: str | None
    taskEnqueuedAt: str | None
    sentToSeerAt: str | None
    reviewStartedAt: str | None
    reviewCompletedAt: str | None
    seerRunId: str | None
    commentsPosted: int | None


class DetailedCodeReviewEventResponse(CodeReviewEventResponse):
    reviewResult: dict | None
    timeline: list[dict]


@register(CodeReviewEvent)
class CodeReviewEventSerializer(Serializer):
    def get_attrs(
        self, item_list: Sequence[CodeReviewEvent], user: Any, **kwargs: Any
    ) -> MutableMapping[CodeReviewEvent, MutableMapping[str, Any]]:
        repo_ids = {item.repository_id for item in item_list}
        repos = {r.id: r for r in Repository.objects.filter(id__in=repo_ids)}

        return {item: {"repository": repos.get(item.repository_id)} for item in item_list}

    def serialize(
        self,
        obj: CodeReviewEvent,
        attrs: MutableMapping[str, Any],
        user: Any,
        **kwargs: Any,
    ) -> CodeReviewEventResponse:
        repo = attrs.get("repository")
        return {
            "id": str(obj.id),
            "organizationId": str(obj.organization_id),
            "repositoryId": str(obj.repository_id),
            "repositoryName": repo.name if repo else None,
            "prNumber": obj.pr_number,
            "prTitle": obj.pr_title,
            "prAuthor": obj.pr_author,
            "prUrl": obj.pr_url,
            "githubEventType": obj.github_event_type,
            "githubEventAction": obj.github_event_action,
            "githubDeliveryId": obj.github_delivery_id,
            "trigger": obj.trigger,
            "triggerUser": obj.trigger_user,
            "triggerAt": _iso_or_none(obj.trigger_at),
            "targetCommitSha": obj.target_commit_sha,
            "status": obj.status,
            "denialReason": obj.denial_reason,
            "dateAdded": obj.date_added.isoformat(),
            "webhookReceivedAt": _iso_or_none(obj.webhook_received_at),
            "preflightCompletedAt": _iso_or_none(obj.preflight_completed_at),
            "taskEnqueuedAt": _iso_or_none(obj.task_enqueued_at),
            "sentToSeerAt": _iso_or_none(obj.sent_to_seer_at),
            "reviewStartedAt": _iso_or_none(obj.review_started_at),
            "reviewCompletedAt": _iso_or_none(obj.review_completed_at),
            "seerRunId": obj.seer_run_id,
            "commentsPosted": obj.comments_posted,
        }


class DetailedCodeReviewEventSerializer(CodeReviewEventSerializer):
    def serialize(
        self,
        obj: CodeReviewEvent,
        attrs: MutableMapping[str, Any],
        user: Any,
        **kwargs: Any,
    ) -> DetailedCodeReviewEventResponse:
        base = super().serialize(obj, attrs, user, **kwargs)

        # Build timeline from timestamps
        timeline = []
        timestamp_stages = [
            ("webhook_received", obj.webhook_received_at),
            ("preflight_completed", obj.preflight_completed_at),
            ("task_enqueued", obj.task_enqueued_at),
            ("sent_to_seer", obj.sent_to_seer_at),
            ("review_started", obj.review_started_at),
            ("review_completed", obj.review_completed_at),
        ]
        for stage, ts in timestamp_stages:
            if ts:
                timeline.append({"stage": stage, "timestamp": ts.isoformat()})

        return {
            **base,
            "reviewResult": obj.review_result,
            "timeline": timeline,
        }
