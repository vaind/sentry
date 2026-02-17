from __future__ import annotations

from django.db.models.functions import Coalesce
from rest_framework.request import Request
from rest_framework.response import Response

from sentry import features
from sentry.api.api_owners import ApiOwner
from sentry.api.api_publish_status import ApiPublishStatus
from sentry.api.base import region_silo_endpoint
from sentry.api.bases.organization import OrganizationEndpoint
from sentry.api.paginator import OffsetPaginator
from sentry.api.serializers import serialize
from sentry.models.code_review_event import CodeReviewEvent
from sentry.seer.code_review.api.serializers.code_review_event import CodeReviewEventSerializer


@region_silo_endpoint
class OrganizationCodeReviewEventsEndpoint(OrganizationEndpoint):
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

        status = request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        trigger_type = request.GET.get("triggerType")
        if trigger_type:
            queryset = queryset.filter(trigger=trigger_type)

        queryset = queryset.annotate(event_time=Coalesce("trigger_at", "date_added"))

        start = request.GET.get("start")
        if start:
            queryset = queryset.filter(event_time__gte=start)

        end = request.GET.get("end")
        if end:
            queryset = queryset.filter(event_time__lte=end)

        return self.paginate(
            request=request,
            queryset=queryset,
            order_by="-event_time",
            paginator_cls=OffsetPaginator,
            on_results=lambda x: serialize(x, request.user, CodeReviewEventSerializer()),
        )
