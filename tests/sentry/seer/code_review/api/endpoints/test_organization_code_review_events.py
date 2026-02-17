from django.urls import reverse
from rest_framework.test import APIClient

from sentry.models.code_review_event import CodeReviewEvent, CodeReviewEventStatus
from sentry.testutils.cases import APITestCase


class OrganizationCodeReviewEventsTest(APITestCase):
    endpoint = "sentry-api-0-organization-code-review-events"

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
            "pr_number": 42,
        }
        defaults.update(kwargs)
        return CodeReviewEvent.objects.create(**defaults)

    def test_requires_feature_flag(self) -> None:
        url = reverse(self.endpoint, args=[self.organization.slug])
        response = self.client.get(url)
        assert response.status_code == 404

    def test_lists_events(self) -> None:
        self._create_event(pr_number=1)
        self._create_event(pr_number=2)

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug])
            response = self.client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 2

    def test_filters_by_status(self) -> None:
        self._create_event(pr_number=1, status=CodeReviewEventStatus.REVIEW_COMPLETED)
        self._create_event(pr_number=2, status=CodeReviewEventStatus.REVIEW_FAILED)

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug])
            response = self.client.get(url, {"status": "review_completed"})

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["status"] == "review_completed"

    def test_filters_by_trigger_type(self) -> None:
        self._create_event(pr_number=1, trigger="on_ready_for_review")
        self._create_event(pr_number=2, trigger="on_new_commit")

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug])
            response = self.client.get(url, {"triggerType": "on_ready_for_review"})

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_filters_by_repository_id(self) -> None:
        other_repo = self.create_repo(project=self.project, name="other/repo")
        self._create_event(pr_number=1, repository_id=self.repo.id)
        self._create_event(pr_number=2, repository_id=other_repo.id)

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug])
            response = self.client.get(url, {"repositoryId": str(self.repo.id)})

        assert response.status_code == 200
        assert len(response.data) == 1

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
            pr_number=99,
        )
        self._create_event(pr_number=1)

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug])
            response = self.client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["prNumber"] == 1

    def test_serializes_repository_name(self) -> None:
        self._create_event(pr_number=1)

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug])
            response = self.client.get(url)

        assert response.status_code == 200
        assert response.data[0]["repositoryName"] == "owner/repo"

    def test_unauthenticated_returns_401(self) -> None:
        anon_client = APIClient()
        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug])
            response = anon_client.get(url)

        assert response.status_code == 401
