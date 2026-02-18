import {useMemo, useState} from 'react';

import {Grid} from '@sentry/scraps/layout';

import * as Layout from 'sentry/components/layouts/thirds';
import {PageHeadingQuestionTooltip} from 'sentry/components/pageHeadingQuestionTooltip';
import SentryDocumentTitle from 'sentry/components/sentryDocumentTitle';
import {t, tct} from 'sentry/locale';
import {parseCursor} from 'sentry/utils/cursor';
import {useApiQuery} from 'sentry/utils/queryClient';
import {useLocation} from 'sentry/utils/useLocation';
import useOrganization from 'sentry/utils/useOrganization';
import {PrReviewFilters} from 'sentry/views/explore/prReview/prReviewFilters';
import {PrReviewList} from 'sentry/views/explore/prReview/prReviewList';
import {PrReviewStats} from 'sentry/views/explore/prReview/prReviewStats';
import type {
  CodeReviewPR,
  CodeReviewStats as CodeReviewStatsType,
} from 'sentry/views/explore/prReview/types';

const TIME_RANGE_TO_MS: Record<string, number> = {
  '24h': 24 * 60 * 60 * 1000,
  '7d': 7 * 24 * 60 * 60 * 1000,
  '14d': 14 * 24 * 60 * 60 * 1000,
  '30d': 30 * 24 * 60 * 60 * 1000,
  '90d': 90 * 24 * 60 * 60 * 1000,
};

export default function PrReviewContent() {
  const organization = useOrganization();
  const location = useLocation();
  const [status, setStatus] = useState('');
  const [repositoryIds, setRepositoryIds] = useState<string[]>([]);
  const [timeRange, setTimeRange] = useState('14d');

  const queryParams: Record<string, string | string[]> = useMemo(() => {
    const params: Record<string, string | string[]> = {};
    if (status) {
      params.status = status;
    }
    if (repositoryIds.length > 0) {
      params.repositoryId = repositoryIds;
    }
    const ms = TIME_RANGE_TO_MS[timeRange];
    if (ms) {
      params.start = new Date(Date.now() - ms).toISOString();
    }
    return params;
  }, [status, repositoryIds, timeRange]);

  const cursorParam =
    typeof location.query.cursor === 'string' ? location.query.cursor : undefined;

  const {
    data: prs,
    isLoading,
    getResponseHeader,
  } = useApiQuery<CodeReviewPR[]>(
    [
      `/organizations/${organization.slug}/code-review-prs/`,
      {query: {...queryParams, ...(cursorParam ? {cursor: cursorParam} : {})}},
    ],
    {staleTime: 30_000}
  );

  const statsQueryParams = useMemo(() => {
    const params = {...queryParams};
    if (timeRange === '24h') {
      params.interval = '1h';
    }
    return params;
  }, [queryParams, timeRange]);

  const {data: stats} = useApiQuery<CodeReviewStatsType>(
    [`/organizations/${organization.slug}/code-review-stats/`, {query: statsQueryParams}],
    {staleTime: 60_000}
  );

  const pageLinks = getResponseHeader?.('Link') ?? null;
  const hitsHeader = getResponseHeader?.('X-Hits');
  const totalHits = hitsHeader ? parseInt(hitsHeader, 10) : undefined;

  const paginationCaption = useMemo(() => {
    if (!totalHits || !prs?.length) {
      return null;
    }
    const cursor = parseCursor(location.query.cursor);
    const page = cursor?.offset ?? 0;
    const perPage = cursor?.value ?? 25;
    const start = page * perPage + 1;
    const end = start + prs.length - 1;
    return tct('[start]-[end] of [total]', {start, end, total: totalHits});
  }, [totalHits, prs?.length, location.query.cursor]);

  return (
    <SentryDocumentTitle title={t('Seer PR Reviews')} orgSlug={organization.slug}>
      <Layout.Page>
        <Layout.Header unified>
          <Layout.HeaderContent unified>
            <Layout.Title>
              {t('Seer PR Reviews')}
              <PageHeadingQuestionTooltip
                docsUrl="https://docs.sentry.io/product/ai-in-sentry/seer/ai-code-review/"
                title={t('Monitor automated code reviews on your pull requests.')}
              />
            </Layout.Title>
          </Layout.HeaderContent>
        </Layout.Header>
        <Layout.Body>
          <Layout.Main width="full">
            <Grid gap="xl" columns="100%">
              <PrReviewFilters
                repositoryIds={repositoryIds}
                repositories={stats?.repositories ?? []}
                status={status}
                timeRange={timeRange}
                onRepositoryChange={setRepositoryIds}
                onStatusChange={setStatus}
                onTimeRangeChange={setTimeRange}
              />
              <PrReviewStats stats={stats} statusFilter={status} timeRange={timeRange} />
              <PrReviewList
                prs={prs}
                isLoading={isLoading}
                pageLinks={pageLinks}
                paginationCaption={paginationCaption}
              />
            </Grid>
          </Layout.Main>
        </Layout.Body>
      </Layout.Page>
    </SentryDocumentTitle>
  );
}
