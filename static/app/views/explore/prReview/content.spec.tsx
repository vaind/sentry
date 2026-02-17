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
      url: `/organizations/${organization.slug}/code-review-prs/`,
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

  it('renders PRs from the API', async () => {
    MockApiClient.addMockResponse({
      url: `/organizations/${organization.slug}/code-review-prs/`,
      body: [
        {
          repositoryId: '10',
          repositoryName: 'owner/repo',
          prNumber: 42,
          prTitle: 'Fix the bug',
          prAuthor: 'testuser',
          prUrl: 'https://github.com/owner/repo/pull/42',
          latestStatus: 'review_completed',
          latestTrigger: 'on_ready_for_review',
          eventCount: 2,
          totalComments: 3,
          lastActivity: '2026-01-15T10:00:00Z',
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

  it('renders empty state when no PRs', async () => {
    MockApiClient.addMockResponse({
      url: `/organizations/${organization.slug}/code-review-prs/`,
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

    expect(await screen.findByText('No pull requests found.')).toBeInTheDocument();
  });

  it('renders stats cards', async () => {
    MockApiClient.addMockResponse({
      url: `/organizations/${organization.slug}/code-review-prs/`,
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
