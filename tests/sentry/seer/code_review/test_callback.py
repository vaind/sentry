from sentry.models.code_review_event import CodeReviewEvent, CodeReviewEventStatus
from sentry.seer.code_review.callback import report_code_review_result
from sentry.testutils.cases import TestCase


class TestReportCodeReviewResult(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.repo = self.create_repo(project=self.project, name="owner/repo")

    def test_updates_event_by_delivery_id(self) -> None:
        record = CodeReviewEvent.objects.create(
            organization_id=self.organization.id,
            repository_id=self.repo.id,
            github_event_type="pull_request",
            github_event_action="opened",
            github_delivery_id="match-by-delivery",
            pr_number=42,
            status=CodeReviewEventStatus.SENT_TO_SEER,
        )

        result = report_code_review_result(
            github_delivery_id="match-by-delivery",
            seer_run_id="seer-run-001",
            status="completed",
            comments_posted=3,
        )

        assert result == {"status": "ok"}
        record.refresh_from_db()
        assert record.status == CodeReviewEventStatus.REVIEW_COMPLETED
        assert record.seer_run_id == "seer-run-001"
        assert record.comments_posted == 3

    def test_returns_not_found_when_no_match(self) -> None:
        result = report_code_review_result(
            github_delivery_id="does-not-exist",
            seer_run_id="seer-run-003",
            status="completed",
            comments_posted=0,
        )

        assert result == {"status": "not_found"}

    def test_maps_failed_status(self) -> None:
        record = CodeReviewEvent.objects.create(
            organization_id=self.organization.id,
            repository_id=self.repo.id,
            github_event_type="pull_request",
            github_event_action="opened",
            github_delivery_id="fail-delivery",
            pr_number=10,
            status=CodeReviewEventStatus.SENT_TO_SEER,
        )

        report_code_review_result(
            github_delivery_id="fail-delivery",
            seer_run_id="seer-run-004",
            status="failed",
            comments_posted=0,
            error_message="Seer internal error",
        )

        record.refresh_from_db()
        assert record.status == CodeReviewEventStatus.REVIEW_FAILED
        assert record.review_result == {"error_message": "Seer internal error"}

    def test_maps_started_status(self) -> None:
        record = CodeReviewEvent.objects.create(
            organization_id=self.organization.id,
            repository_id=self.repo.id,
            github_event_type="pull_request",
            github_event_action="opened",
            github_delivery_id="started-delivery",
            pr_number=11,
            status=CodeReviewEventStatus.SENT_TO_SEER,
        )

        report_code_review_result(
            github_delivery_id="started-delivery",
            seer_run_id="seer-run-005",
            status="started",
            comments_posted=0,
            started_at="2026-01-15T10:00:00+00:00",
        )

        record.refresh_from_db()
        assert record.status == CodeReviewEventStatus.REVIEW_STARTED
        assert record.review_started_at is not None

    def test_parses_timestamps(self) -> None:
        record = CodeReviewEvent.objects.create(
            organization_id=self.organization.id,
            repository_id=self.repo.id,
            github_event_type="pull_request",
            github_event_action="opened",
            github_delivery_id="ts-delivery",
            pr_number=12,
            status=CodeReviewEventStatus.SENT_TO_SEER,
        )

        report_code_review_result(
            github_delivery_id="ts-delivery",
            seer_run_id="seer-run-006",
            status="completed",
            comments_posted=5,
            started_at="2026-01-15T10:00:00+00:00",
            completed_at="2026-01-15T10:05:00+00:00",
        )

        record.refresh_from_db()
        assert record.review_started_at is not None
        assert record.review_completed_at is not None

    def test_ignores_invalid_timestamps(self) -> None:
        record = CodeReviewEvent.objects.create(
            organization_id=self.organization.id,
            repository_id=self.repo.id,
            github_event_type="pull_request",
            github_event_action="opened",
            github_delivery_id="bad-ts-delivery",
            pr_number=13,
            status=CodeReviewEventStatus.SENT_TO_SEER,
        )

        report_code_review_result(
            github_delivery_id="bad-ts-delivery",
            seer_run_id="seer-run-007",
            status="completed",
            comments_posted=0,
            started_at="not-a-date",
            completed_at="also-not-a-date",
        )

        record.refresh_from_db()
        assert record.status == CodeReviewEventStatus.REVIEW_COMPLETED
        assert record.review_started_at is None
        assert record.review_completed_at is None
