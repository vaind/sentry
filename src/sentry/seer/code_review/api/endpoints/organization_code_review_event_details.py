from __future__ import annotations

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
from sentry.seer.code_review.api.serializers.code_review_event import (
    DetailedCodeReviewEventSerializer,
)
from sentry.seer.code_review.rpc_queries import get_pr_comments


@region_silo_endpoint
class OrganizationCodeReviewEventDetailsEndpoint(OrganizationEndpoint):
    owner = ApiOwner.ML_AI
    publish_status = {
        "GET": ApiPublishStatus.EXPERIMENTAL,
    }

    def get(self, request: Request, organization, event_id: int) -> Response:
        if not features.has("organizations:pr-review-dashboard", organization, actor=request.user):
            return Response(status=404)

        try:
            event = CodeReviewEvent.objects.get(
                id=event_id,
                organization_id=organization.id,
            )
        except CodeReviewEvent.DoesNotExist:
            return Response(status=404)

        result = serialize(event, request.user, DetailedCodeReviewEventSerializer())

        comments_error = False
        comments = None
        if event.pr_number:
            try:
                repo = Repository.objects.get(id=event.repository_id)
                repo_name_parts = repo.name.split("/", 1)
                if len(repo_name_parts) == 2:
                    owner, repo_name = repo_name_parts
                    comments = get_pr_comments("github", owner, repo_name, event.pr_number)
                    if comments is None:
                        comments_error = True
            except Repository.DoesNotExist:
                comments_error = True

        result["comments"] = comments or []
        result["commentsError"] = comments_error

        return Response(result)
