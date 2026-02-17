from __future__ import annotations

from django.db.models.functions import Coalesce
from rest_framework.request import Request
from rest_framework.response import Response

from sentry import features
from sentry.api.api_owners import ApiOwner
from sentry.api.api_publish_status import ApiPublishStatus
from sentry.api.base import region_silo_endpoint
from sentry.api.bases.organization import OrganizationEndpoint
from sentry.api.serializers import serialize
from sentry.models.code_review_event import CodeReviewEvent
from sentry.models.repository import Repository
from sentry.seer.code_review.api.serializers.code_review_event import CodeReviewEventSerializer
from sentry.seer.code_review.rpc_queries import get_pr_comments


def _fetch_pr_comments(repo_id: int, pr_number: int) -> tuple[list[dict], bool]:
    """Fetch PR comments from Seer. Returns (comments, has_error)."""
    try:
        repo = Repository.objects.get(id=repo_id)
    except Repository.DoesNotExist:
        return [], True

    repo_name_parts = repo.name.split("/", 1)
    if len(repo_name_parts) != 2:
        return [], False

    owner, repo_name = repo_name_parts
    comments = get_pr_comments("github", owner, repo_name, pr_number)
    if comments is None:
        return [], True

    return comments, False


@region_silo_endpoint
class OrganizationCodeReviewPRDetailsEndpoint(OrganizationEndpoint):
    owner = ApiOwner.CODING_WORKFLOWS
    publish_status = {
        "GET": ApiPublishStatus.EXPERIMENTAL,
    }

    def get(self, request: Request, organization, repo_id: str, pr_number: str) -> Response:
        if not features.has("organizations:pr-review-dashboard", organization, actor=request.user):
            return Response(status=404)

        repo_id_int = int(repo_id)
        pr_number_int = int(pr_number)

        events = (
            CodeReviewEvent.objects.filter(
                organization_id=organization.id,
                repository_id=repo_id_int,
                pr_number=pr_number_int,
            )
            .annotate(event_time=Coalesce("trigger_at", "date_added"))
            .order_by("-event_time")
        )

        if not events.exists():
            return Response(status=404)

        latest_event = events[0]

        try:
            repo = Repository.objects.get(id=repo_id_int)
            repo_name = repo.name
        except Repository.DoesNotExist:
            repo_name = None

        comments, comments_error = _fetch_pr_comments(repo_id_int, pr_number_int)

        return Response(
            {
                "repositoryId": str(repo_id_int),
                "repositoryName": repo_name,
                "prNumber": pr_number_int,
                "prTitle": latest_event.pr_title,
                "prAuthor": latest_event.pr_author,
                "prUrl": latest_event.pr_url,
                "prState": latest_event.pr_state,
                "events": serialize(list(events), request.user, CodeReviewEventSerializer()),
                "comments": comments,
                "commentsError": comments_error,
            }
        )
