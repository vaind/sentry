from __future__ import annotations

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce, TruncDay
from rest_framework.request import Request
from rest_framework.response import Response

from sentry import features
from sentry.api.api_owners import ApiOwner
from sentry.api.api_publish_status import ApiPublishStatus
from sentry.api.base import region_silo_endpoint
from sentry.api.bases.organization import OrganizationEndpoint
from sentry.models.code_review_event import CodeReviewEvent, CodeReviewEventStatus

SKIPPED_STATUSES = Q(status=CodeReviewEventStatus.PREFLIGHT_DENIED) | Q(
    status=CodeReviewEventStatus.WEBHOOK_FILTERED
)
REVIEWED_STATUSES = Q(status=CodeReviewEventStatus.REVIEW_COMPLETED)


@region_silo_endpoint
class OrganizationCodeReviewStatsEndpoint(OrganizationEndpoint):
    owner = ApiOwner.CODING_WORKFLOWS
    publish_status = {
        "GET": ApiPublishStatus.EXPERIMENTAL,
    }

    def get(self, request: Request, organization) -> Response:
        if not features.has("organizations:pr-review-dashboard", organization, actor=request.user):
            return Response(status=404)

        queryset = CodeReviewEvent.objects.filter(organization_id=organization.id)

        repository_id = request.GET.get("repositoryId")
        if repository_id:
            queryset = queryset.filter(repository_id=repository_id)

        queryset = queryset.annotate(event_time=Coalesce("trigger_at", "date_added"))

        start = request.GET.get("start")
        if start:
            queryset = queryset.filter(event_time__gte=start)

        end = request.GET.get("end")
        if end:
            queryset = queryset.filter(event_time__lte=end)

        # Event-level counts
        review_events = queryset.filter(REVIEWED_STATUSES)
        total_reviews = review_events.count()
        total_comments = review_events.aggregate(total=Coalesce(Sum("comments_posted"), 0))["total"]

        # PR-level stats: count distinct PRs by their latest event status
        pr_stats = (
            queryset.filter(pr_number__isnull=False)
            .values("repository_id", "pr_number")
            .annotate(
                has_reviewed=Count("id", filter=REVIEWED_STATUSES),
                has_skipped=Count("id", filter=SKIPPED_STATUSES),
            )
        )

        total_prs = 0
        reviewed_prs = 0
        skipped_prs = 0
        for pr in pr_stats:
            total_prs += 1
            if pr["has_reviewed"] > 0:
                reviewed_prs += 1
            # A PR is "skipped" only if it was never reviewed
            if pr["has_skipped"] > 0 and pr["has_reviewed"] == 0:
                skipped_prs += 1

        time_series = (
            queryset.annotate(day=TruncDay("event_time"))
            .values("day")
            .annotate(
                reviewed=Count("id", filter=REVIEWED_STATUSES),
                skipped=Count("id", filter=SKIPPED_STATUSES),
                comments=Coalesce(Sum("comments_posted", filter=REVIEWED_STATUSES), 0),
            )
            .order_by("day")
        )

        return Response(
            {
                "stats": {
                    "totalPrs": total_prs,
                    "totalReviews": total_reviews,
                    "totalComments": total_comments,
                    "skippedPrs": skipped_prs,
                },
                "timeSeries": [
                    {
                        "date": entry["day"].isoformat(),
                        "reviewed": entry["reviewed"],
                        "skipped": entry["skipped"],
                        "comments": entry["comments"],
                    }
                    for entry in time_series
                ],
            }
        )
