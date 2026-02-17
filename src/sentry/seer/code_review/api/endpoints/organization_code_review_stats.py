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

        stats = queryset.aggregate(
            total=Count("id"),
            completed=Count("id", filter=Q(status=CodeReviewEventStatus.REVIEW_COMPLETED)),
            failed=Count("id", filter=Q(status=CodeReviewEventStatus.REVIEW_FAILED)),
            preflight_denied=Count("id", filter=Q(status=CodeReviewEventStatus.PREFLIGHT_DENIED)),
            webhook_filtered=Count("id", filter=Q(status=CodeReviewEventStatus.WEBHOOK_FILTERED)),
            total_comments=Sum("comments_posted"),
        )

        time_series = (
            queryset.annotate(day=TruncDay("event_time"))
            .values("day")
            .annotate(
                count=Count("id"),
                completed=Count("id", filter=Q(status=CodeReviewEventStatus.REVIEW_COMPLETED)),
                failed=Count("id", filter=Q(status=CodeReviewEventStatus.REVIEW_FAILED)),
            )
            .order_by("day")
        )

        return Response(
            {
                "stats": {
                    "total": stats["total"],
                    "completed": stats["completed"],
                    "failed": stats["failed"],
                    "preflightDenied": stats["preflight_denied"],
                    "webhookFiltered": stats["webhook_filtered"],
                    "totalComments": stats["total_comments"] or 0,
                },
                "timeSeries": [
                    {
                        "date": entry["day"].isoformat(),
                        "count": entry["count"],
                        "completed": entry["completed"],
                        "failed": entry["failed"],
                    }
                    for entry in time_series
                ],
            }
        )
