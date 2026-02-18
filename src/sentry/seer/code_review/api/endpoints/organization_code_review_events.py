from __future__ import annotations

from django.db.models import Count, Max, Sum
from django.db.models.functions import Coalesce
from rest_framework.request import Request
from rest_framework.response import Response

from sentry import features
from sentry.api.api_owners import ApiOwner
from sentry.api.api_publish_status import ApiPublishStatus
from sentry.api.base import region_silo_endpoint
from sentry.api.bases.organization import OrganizationEndpoint
from sentry.api.paginator import OffsetPaginator
from sentry.models.code_review_event import CodeReviewEvent
from sentry.models.repository import Repository


@region_silo_endpoint
class OrganizationCodeReviewPRsEndpoint(OrganizationEndpoint):
    owner = ApiOwner.CODING_WORKFLOWS
    publish_status = {
        "GET": ApiPublishStatus.EXPERIMENTAL,
    }

    def get(self, request: Request, organization) -> Response:
        if not features.has("organizations:pr-review-dashboard", organization, actor=request.user):
            return Response(status=404)

        queryset = CodeReviewEvent.objects.filter(organization_id=organization.id)

        repository_ids = request.GET.getlist("repositoryId")
        if repository_ids:
            queryset = queryset.filter(repository_id__in=repository_ids)

        status = request.GET.get("status")
        if status:
            queryset = queryset.filter(pr_state=status)

        trigger_type = request.GET.get("triggerType")
        if trigger_type:
            queryset = queryset.filter(trigger=trigger_type)

        start = request.GET.get("start")
        if start:
            queryset = queryset.filter(trigger_at__gte=start)

        end = request.GET.get("end")
        if end:
            queryset = queryset.filter(trigger_at__lte=end)

        pr_groups = (
            queryset.filter(pr_number__isnull=False)
            .values("repository_id", "pr_number")
            .annotate(
                event_count=Count("id"),
                total_comments=Coalesce(Sum("comments_posted"), 0),
                last_activity=Max("trigger_at"),
            )
            .order_by("-last_activity")
        )

        return self.paginate(
            request=request,
            queryset=pr_groups,
            order_by="-last_activity",
            paginator_cls=OffsetPaginator,
            default_per_page=25,
            count_hits=True,
            on_results=lambda groups: self._enrich_groups(groups, queryset),
        )

    def _enrich_groups(self, groups: list[dict], base_queryset) -> list[dict]:
        """Attach latest event metadata (title, author, status) to each PR group."""
        if not groups:
            return []

        repo_ids = {g["repository_id"] for g in groups}
        repos = {r.id: r for r in Repository.objects.filter(id__in=repo_ids)}

        pr_keys = [(g["repository_id"], g["pr_number"]) for g in groups]
        latest_event_ids = []
        for repo_id, pr_num in pr_keys:
            latest = (
                base_queryset.filter(repository_id=repo_id, pr_number=pr_num)
                .order_by("-trigger_at")
                .values_list("id", flat=True)
                .first()
            )
            if latest:
                latest_event_ids.append(latest)

        latest_events_by_key = {}
        for event in CodeReviewEvent.objects.filter(id__in=latest_event_ids):
            latest_events_by_key[(event.repository_id, event.pr_number)] = event

        results = []
        for group in groups:
            repo_id = group["repository_id"]
            pr_number = group["pr_number"]
            repo = repos.get(repo_id)
            latest_event = latest_events_by_key.get((repo_id, pr_number))

            results.append(
                {
                    "repositoryId": str(repo_id),
                    "repositoryName": repo.name if repo else None,
                    "prNumber": pr_number,
                    "prTitle": latest_event.pr_title if latest_event else None,
                    "prAuthor": latest_event.pr_author if latest_event else None,
                    "prUrl": latest_event.pr_url if latest_event else None,
                    "prState": latest_event.pr_state if latest_event else None,
                    "latestStatus": latest_event.status if latest_event else None,
                    "latestTrigger": latest_event.trigger if latest_event else None,
                    "eventCount": group["event_count"],
                    "totalComments": group["total_comments"],
                    "lastActivity": group["last_activity"].isoformat()
                    if group["last_activity"]
                    else None,
                }
            )

        return results
