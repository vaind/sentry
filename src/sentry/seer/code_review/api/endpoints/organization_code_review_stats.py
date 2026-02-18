from __future__ import annotations

from django.db.models import CharField, Count, Q, Sum, Value
from django.db.models.functions import Cast, Coalesce, Concat, TruncDay, TruncHour
from rest_framework.request import Request
from rest_framework.response import Response

from sentry import features
from sentry.api.api_owners import ApiOwner
from sentry.api.api_publish_status import ApiPublishStatus
from sentry.api.base import region_silo_endpoint
from sentry.api.bases.organization import OrganizationEndpoint
from sentry.models.code_review_event import CodeReviewEvent, CodeReviewEventStatus
from sentry.models.repository import Repository

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

        base_queryset = CodeReviewEvent.objects.filter(organization_id=organization.id)

        # Distinct repos with code review events (always unfiltered)
        repo_ids = base_queryset.values_list("repository_id", flat=True).distinct()
        repos = Repository.objects.filter(id__in=repo_ids)
        repositories = [{"id": str(r.id), "name": r.name} for r in repos.order_by("name")]

        queryset = base_queryset

        repository_ids = request.GET.getlist("repositoryId")
        if repository_ids:
            queryset = queryset.filter(repository_id__in=repository_ids)

        pr_state = request.GET.get("status")
        if pr_state:
            queryset = queryset.filter(pr_state=pr_state)

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

        # Author stats: distinct authors and top authors by PR count
        author_prs = (
            queryset.filter(pr_number__isnull=False, pr_author__isnull=False)
            .exclude(pr_author="")
            .values("pr_author")
            .annotate(
                pr_count=Count(
                    Concat(
                        Cast("repository_id", output_field=CharField()),
                        Value("-"),
                        Cast("pr_number", output_field=CharField()),
                    ),
                    distinct=True,
                )
            )
            .order_by("-pr_count")
        )
        total_authors = author_prs.count()
        top_authors = [
            {"author": entry["pr_author"], "prCount": entry["pr_count"]} for entry in author_prs[:3]
        ]

        interval = request.GET.get("interval", "1d")
        trunc_fn = TruncHour if interval == "1h" else TruncDay

        time_series = (
            queryset.annotate(bucket=trunc_fn("event_time"))
            .values("bucket")
            .annotate(
                prs=Count(
                    Concat(
                        Cast("repository_id", output_field=CharField()),
                        Value("-"),
                        Cast("pr_number", output_field=CharField()),
                    ),
                    distinct=True,
                    filter=Q(pr_number__isnull=False),
                ),
                reviewed=Count("id", filter=REVIEWED_STATUSES),
                skipped=Count("id", filter=SKIPPED_STATUSES),
                comments=Coalesce(Sum("comments_posted", filter=REVIEWED_STATUSES), 0),
            )
            .order_by("bucket")
        )

        return Response(
            {
                "repositories": repositories,
                "stats": {
                    "totalPrs": total_prs,
                    "totalReviews": total_reviews,
                    "totalComments": total_comments,
                    "skippedPrs": skipped_prs,
                    "totalAuthors": total_authors,
                    "topAuthors": top_authors,
                },
                "timeSeries": [
                    {
                        "date": entry["bucket"].isoformat(),
                        "prs": entry["prs"],
                        "reviewed": entry["reviewed"],
                        "skipped": entry["skipped"],
                        "comments": entry["comments"],
                    }
                    for entry in time_series
                ],
            }
        )
