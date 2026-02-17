import {OrganizationFixture} from 'sentry-fixture/organization';

import {render, screen} from 'sentry-test/reactTestingLibrary';

import {PrReviewList} from 'sentry/views/explore/prReview/prReviewList';
import type {CodeReviewEvent} from 'sentry/views/explore/prReview/types';

describe('PrReviewList', () => {
  const organization = OrganizationFixture();

  const mockEvent: CodeReviewEvent = {
    id: '1',
    organizationId: '1',
    repositoryId: '10',
    repositoryName: 'owner/repo',
    prNumber: 42,
    prTitle: 'Fix the bug',
    prAuthor: 'testuser',
    prUrl: 'https://github.com/owner/repo/pull/42',
    githubEventType: 'pull_request',
    githubEventAction: 'opened',
    githubDeliveryId: 'abc-123',
    trigger: 'on_ready_for_review',
    triggerUser: null,
    triggerAt: null,
    targetCommitSha: null,
    status: 'review_completed',
    denialReason: null,
    dateAdded: '2026-01-15T10:00:00Z',
    webhookReceivedAt: null,
    taskEnqueuedAt: null,
    sentToSeerAt: null,
    reviewStartedAt: null,
    reviewCompletedAt: null,
    seerRunId: null,
    commentsPosted: 3,
  };

  it('renders events in the table', () => {
    render(<PrReviewList events={[mockEvent]} isLoading={false} pageLinks={null} />, {
      organization,
    });

    expect(screen.getByText('owner/repo')).toBeInTheDocument();
    expect(screen.getByText('#42')).toBeInTheDocument();
    expect(screen.getByText('Fix the bug')).toBeInTheDocument();
    expect(screen.getByText('Review Completed')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('renders empty message when no events', () => {
    render(<PrReviewList events={[]} isLoading={false} pageLinks={null} />, {
      organization,
    });

    expect(screen.getByText('No code review events found.')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    render(<PrReviewList events={undefined} isLoading pageLinks={null} />, {
      organization,
    });

    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  it('renders table headers', () => {
    render(<PrReviewList events={[mockEvent]} isLoading={false} pageLinks={null} />, {
      organization,
    });

    expect(screen.getByText('Repository')).toBeInTheDocument();
    expect(screen.getByText('PR')).toBeInTheDocument();
    expect(screen.getByText('Trigger')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Time')).toBeInTheDocument();
    expect(screen.getByText('Comments')).toBeInTheDocument();
  });
});
