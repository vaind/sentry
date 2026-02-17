import {OrganizationFixture} from 'sentry-fixture/organization';

import {render, screen, waitFor} from 'sentry-test/reactTestingLibrary';

import PrReviewContent from 'sentry/views/explore/prReview/content';

describe('PrReviewContent', () => {
  const organization = OrganizationFixture({
    features: ['pr-review-dashboard'],
  });

  beforeEach(() => {
    MockApiClient.clearMockResponses();
  });

  it('renders the page title and header', async () => {
    MockApiClient.addMockResponse({
      url: `/organizations/${organization.slug}/code-review-events/`,
      body: [],
    });
    MockApiClient.addMockResponse({
      url: `/organizations/${organization.slug}/code-review-stats/`,
      body: {
        stats: {
          total: 0,
          completed: 0,
          failed: 0,
          preflightDenied: 0,
          webhookFiltered: 0,
          totalComments: 0,
        },
        timeSeries: [],
      },
    });

    render(<PrReviewContent />, {organization});

    expect(await screen.findByText('PR Reviews')).toBeInTheDocument();
  });

  it('renders events from the API', async () => {
    MockApiClient.addMockResponse({
      url: `/organizations/${organization.slug}/code-review-events/`,
      body: [
        {
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
          preflightCompletedAt: null,
          taskEnqueuedAt: null,
          sentToSeerAt: null,
          reviewStartedAt: null,
          reviewCompletedAt: null,
          seerRunId: null,
          commentsPosted: 3,
        },
      ],
    });
    MockApiClient.addMockResponse({
      url: `/organizations/${organization.slug}/code-review-stats/`,
      body: {
        stats: {
          total: 1,
          completed: 1,
          failed: 0,
          preflightDenied: 0,
          webhookFiltered: 0,
          totalComments: 3,
        },
        timeSeries: [],
      },
    });

    render(<PrReviewContent />, {organization});

    expect(await screen.findByText('Fix the bug')).toBeInTheDocument();
    expect(screen.getByText('#42')).toBeInTheDocument();
    expect(screen.getByText('owner/repo')).toBeInTheDocument();
  });

  it('renders empty state when no events', async () => {
    MockApiClient.addMockResponse({
      url: `/organizations/${organization.slug}/code-review-events/`,
      body: [],
    });
    MockApiClient.addMockResponse({
      url: `/organizations/${organization.slug}/code-review-stats/`,
      body: {
        stats: {
          total: 0,
          completed: 0,
          failed: 0,
          preflightDenied: 0,
          webhookFiltered: 0,
          totalComments: 0,
        },
        timeSeries: [],
      },
    });

    render(<PrReviewContent />, {organization});

    expect(await screen.findByText('No code review events found.')).toBeInTheDocument();
  });

  it('renders stats cards', async () => {
    MockApiClient.addMockResponse({
      url: `/organizations/${organization.slug}/code-review-events/`,
      body: [],
    });
    MockApiClient.addMockResponse({
      url: `/organizations/${organization.slug}/code-review-stats/`,
      body: {
        stats: {
          total: 10,
          completed: 7,
          failed: 1,
          preflightDenied: 1,
          webhookFiltered: 1,
          totalComments: 25,
        },
        timeSeries: [],
      },
    });

    render(<PrReviewContent />, {organization});

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument();
    });
    expect(screen.getByText('Total Reviews')).toBeInTheDocument();
  });
});
