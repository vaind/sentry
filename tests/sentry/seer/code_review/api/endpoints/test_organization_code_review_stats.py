from django.urls import reverse

from sentry.models.code_review_event import CodeReviewEvent, CodeReviewEventStatus
from sentry.testutils.cases import APITestCase


class OrganizationCodeReviewStatsTest(APITestCase):
    endpoint = "sentry-api-0-organization-code-review-stats"

    def setUp(self) -> None:
        super().setUp()
        self.repo = self.create_repo(project=self.project, name="owner/repo")
        self.login_as(user=self.user)

    def _create_event(self, **kwargs) -> CodeReviewEvent:
        defaults = {
            "organization_id": self.organization.id,
            "repository_id": self.repo.id,
            "github_event_type": "pull_request",
            "github_event_action": "opened",
            "status": CodeReviewEventStatus.REVIEW_COMPLETED,
        }
        defaults.update(kwargs)
        return CodeReviewEvent.objects.create(**defaults)

    def test_requires_feature_flag(self) -> None:
        url = reverse(self.endpoint, args=[self.organization.slug])
        response = self.client.get(url)
        assert response.status_code == 404

    def test_returns_aggregated_stats(self) -> None:
        self._create_event(status=CodeReviewEventStatus.REVIEW_COMPLETED, comments_posted=3)
        self._create_event(status=CodeReviewEventStatus.REVIEW_COMPLETED, comments_posted=2)
        self._create_event(status=CodeReviewEventStatus.REVIEW_FAILED)
        self._create_event(status=CodeReviewEventStatus.PREFLIGHT_DENIED)
        self._create_event(status=CodeReviewEventStatus.WEBHOOK_FILTERED)

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug])
            response = self.client.get(url)

        assert response.status_code == 200
        stats = response.data["stats"]
        assert stats["total"] == 5
        assert stats["completed"] == 2
        assert stats["failed"] == 1
        assert stats["preflightDenied"] == 1
        assert stats["webhookFiltered"] == 1
        assert stats["totalComments"] == 5

    def test_returns_time_series(self) -> None:
        self._create_event(status=CodeReviewEventStatus.REVIEW_COMPLETED)

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug])
            response = self.client.get(url)

        assert response.status_code == 200
        assert len(response.data["timeSeries"]) >= 1
        entry = response.data["timeSeries"][0]
        assert "date" in entry
        assert "count" in entry
        assert "completed" in entry
        assert "failed" in entry

    def test_empty_stats(self) -> None:
        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug])
            response = self.client.get(url)

        assert response.status_code == 200
        stats = response.data["stats"]
        assert stats["total"] == 0
        assert stats["totalComments"] == 0

    def test_does_not_leak_cross_org(self) -> None:
        other_org = self.create_organization(owner=self.create_user())
        other_repo = self.create_repo(
            project=self.create_project(organization=other_org), name="other/repo"
        )
        CodeReviewEvent.objects.create(
            organization_id=other_org.id,
            repository_id=other_repo.id,
            github_event_type="pull_request",
            github_event_action="opened",
            status=CodeReviewEventStatus.REVIEW_COMPLETED,
            comments_posted=10,
        )

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug])
            response = self.client.get(url)

        assert response.status_code == 200
        assert response.data["stats"]["total"] == 0
        assert response.data["stats"]["totalComments"] == 0

    def test_filters_by_repository_id(self) -> None:
        other_repo = self.create_repo(project=self.project, name="other/repo")
        self._create_event(
            repository_id=self.repo.id,
            status=CodeReviewEventStatus.REVIEW_COMPLETED,
            comments_posted=5,
        )
        self._create_event(
            repository_id=other_repo.id,
            status=CodeReviewEventStatus.REVIEW_COMPLETED,
            comments_posted=3,
        )

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug])
            response = self.client.get(url, {"repositoryId": str(self.repo.id)})

        assert response.status_code == 200
        assert response.data["stats"]["total"] == 1
        assert response.data["stats"]["totalComments"] == 5
