from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from sentry.models.code_review_event import CodeReviewEvent, CodeReviewEventStatus
from sentry.testutils.cases import APITestCase


class OrganizationCodeReviewEventDetailsTest(APITestCase):
    endpoint = "sentry-api-0-organization-code-review-event-details"

    def setUp(self) -> None:
        super().setUp()
        self.repo = self.create_repo(
            project=self.project, name="owner/repo", external_id="gh-12345"
        )
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
        event = self._create_event()
        url = reverse(self.endpoint, args=[self.organization.slug, event.id])
        response = self.client.get(url)
        assert response.status_code == 404

    @patch(
        "sentry.seer.code_review.api.endpoints.organization_code_review_event_details.get_pr_comments"
    )
    def test_returns_event_details(self, mock_get_comments) -> None:
        mock_get_comments.return_value = []
        event = self._create_event(pr_title="Fix a bug")

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug, event.id])
            response = self.client.get(url)

        assert response.status_code == 200
        assert response.data["id"] == str(event.id)
        assert response.data["prTitle"] == "Fix a bug"
        assert response.data["repositoryName"] == "owner/repo"
        assert response.data["comments"] == []
        assert response.data["commentsError"] is False

    @patch(
        "sentry.seer.code_review.api.endpoints.organization_code_review_event_details.get_pr_comments"
    )
    def test_fetches_comments_from_seer(self, mock_get_comments) -> None:
        mock_get_comments.return_value = [
            {"body": "Use a constant here", "file": "main.py", "line": 10, "run_id": "run-1"}
        ]
        event = self._create_event(pr_number=42)

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug, event.id])
            response = self.client.get(url)

        assert response.status_code == 200
        assert len(response.data["comments"]) == 1
        assert response.data["comments"][0]["body"] == "Use a constant here"
        assert response.data["commentsError"] is False
        mock_get_comments.assert_called_once_with("github", "owner", "repo", 42)

    @patch(
        "sentry.seer.code_review.api.endpoints.organization_code_review_event_details.get_pr_comments"
    )
    def test_handles_seer_comments_failure(self, mock_get_comments) -> None:
        mock_get_comments.return_value = None
        event = self._create_event(pr_number=42)

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug, event.id])
            response = self.client.get(url)

        assert response.status_code == 200
        assert response.data["comments"] == []
        assert response.data["commentsError"] is True

    def test_returns_404_for_nonexistent(self) -> None:
        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug, 99999999])
            response = self.client.get(url)

        assert response.status_code == 404

    def test_does_not_leak_cross_org(self) -> None:
        other_org = self.create_organization(owner=self.create_user())
        other_repo = self.create_repo(
            project=self.create_project(organization=other_org), name="other/repo"
        )
        event = CodeReviewEvent.objects.create(
            organization_id=other_org.id,
            repository_id=other_repo.id,
            github_event_type="pull_request",
            github_event_action="opened",
            status=CodeReviewEventStatus.REVIEW_COMPLETED,
            pr_number=99,
        )

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug, event.id])
            response = self.client.get(url)

        assert response.status_code == 404

    @patch(
        "sentry.seer.code_review.api.endpoints.organization_code_review_event_details.get_pr_comments"
    )
    def test_includes_timeline(self, mock_get_comments) -> None:
        mock_get_comments.return_value = []
        now = timezone.now()
        event = self._create_event(
            webhook_received_at=now,
            task_enqueued_at=now,
            sent_to_seer_at=now,
            review_completed_at=now,
        )

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug, event.id])
            response = self.client.get(url)

        assert response.status_code == 200
        assert len(response.data["timeline"]) == 4
