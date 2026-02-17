from unittest.mock import patch

from django.urls import reverse

from sentry.models.code_review_event import CodeReviewEvent, CodeReviewEventStatus
from sentry.testutils.cases import APITestCase


class OrganizationCodeReviewPRDetailsTest(APITestCase):
    endpoint = "sentry-api-0-organization-code-review-pr-details"

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
        self._create_event()
        url = reverse(self.endpoint, args=[self.organization.slug, self.repo.id, 42])
        response = self.client.get(url)
        assert response.status_code == 404

    @patch(
        "sentry.seer.code_review.api.endpoints.organization_code_review_event_details.get_pr_comments"
    )
    def test_returns_pr_details_with_events(self, mock_get_comments) -> None:
        mock_get_comments.return_value = []
        self._create_event(pr_title="Fix a bug", pr_number=42)
        self._create_event(pr_title="Fix a bug", pr_number=42, trigger="on_new_commit")

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug, self.repo.id, 42])
            response = self.client.get(url)

        assert response.status_code == 200
        assert response.data["prTitle"] == "Fix a bug"
        assert response.data["prNumber"] == 42
        assert response.data["repositoryName"] == "owner/repo"
        assert response.data["repositoryId"] == str(self.repo.id)
        assert len(response.data["events"]) == 2
        assert response.data["comments"] == []
        assert response.data["commentsError"] is False

    @patch(
        "sentry.seer.code_review.api.endpoints.organization_code_review_event_details.get_pr_comments"
    )
    def test_fetches_comments_from_seer(self, mock_get_comments) -> None:
        mock_get_comments.return_value = [
            {"body": "Use a constant here", "file": "main.py", "line": 10, "run_id": "run-1"}
        ]
        self._create_event(pr_number=42)

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug, self.repo.id, 42])
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
        self._create_event(pr_number=42)

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug, self.repo.id, 42])
            response = self.client.get(url)

        assert response.status_code == 200
        assert response.data["comments"] == []
        assert response.data["commentsError"] is True

    def test_returns_404_for_nonexistent_pr(self) -> None:
        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug, self.repo.id, 99999])
            response = self.client.get(url)

        assert response.status_code == 404

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
            pr_number=42,
        )

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug, other_repo.id, 42])
            response = self.client.get(url)

        assert response.status_code == 404

    @patch(
        "sentry.seer.code_review.api.endpoints.organization_code_review_event_details.get_pr_comments"
    )
    def test_events_ordered_by_time_descending(self, mock_get_comments) -> None:
        mock_get_comments.return_value = []
        e1 = self._create_event(pr_number=42, trigger="on_ready_for_review")
        e2 = self._create_event(pr_number=42, trigger="on_new_commit")

        with self.feature("organizations:pr-review-dashboard"):
            url = reverse(self.endpoint, args=[self.organization.slug, self.repo.id, 42])
            response = self.client.get(url)

        assert response.status_code == 200
        event_ids = [e["id"] for e in response.data["events"]]
        # Most recent first (e2 was created after e1)
        assert event_ids == [str(e2.id), str(e1.id)]
