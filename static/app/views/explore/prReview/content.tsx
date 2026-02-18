import {useState} from 'react';

import {Grid} from '@sentry/scraps/layout';

import * as Layout from 'sentry/components/layouts/thirds';
import {PageHeadingQuestionTooltip} from 'sentry/components/pageHeadingQuestionTooltip';
import SentryDocumentTitle from 'sentry/components/sentryDocumentTitle';
import {t} from 'sentry/locale';
import {useApiQuery} from 'sentry/utils/queryClient';
import useOrganization from 'sentry/utils/useOrganization';
import {PrReviewFilters} from 'sentry/views/explore/prReview/prReviewFilters';
import {PrReviewList} from 'sentry/views/explore/prReview/prReviewList';
import {PrReviewStats} from 'sentry/views/explore/prReview/prReviewStats';
import type {
  CodeReviewPR,
  CodeReviewStats as CodeReviewStatsType,
} from 'sentry/views/explore/prReview/types';

export default function PrReviewContent() {
  const organization = useOrganization();
  const [status, setStatus] = useState('');
  const [triggerType, setTriggerType] = useState('');

  const queryParams: Record<string, string> = {};
  if (status) {
    queryParams.status = status;
  }
  if (triggerType) {
    queryParams.triggerType = triggerType;
  }

  const {
    data: prs,
    isLoading,
    getResponseHeader,
  } = useApiQuery<CodeReviewPR[]>(
    [`/organizations/${organization.slug}/code-review-prs/`, {query: queryParams}],
    {staleTime: 30_000}
  );

  const {data: stats} = useApiQuery<CodeReviewStatsType>(
    [`/organizations/${organization.slug}/code-review-stats/`, {query: queryParams}],
    {staleTime: 60_000}
  );

  const pageLinks = getResponseHeader?.('Link') ?? null;

  return (
    <SentryDocumentTitle title={t('PR Reviews')} orgSlug={organization.slug}>
      <Layout.Page>
        <Layout.Header unified>
          <Layout.HeaderContent unified>
            <Layout.Title>
              {t('PR Reviews')}
              <PageHeadingQuestionTooltip
                docsUrl="https://docs.sentry.io/product/explore/pr-reviews/"
                title={t('Monitor automated code reviews on your pull requests.')}
              />
            </Layout.Title>
          </Layout.HeaderContent>
        </Layout.Header>
        <Layout.Body>
          <Layout.Main width="full">
            <Grid gap="xl" columns="100%">
              <PrReviewFilters
                status={status}
                triggerType={triggerType}
                onStatusChange={setStatus}
                onTriggerTypeChange={setTriggerType}
              />
              <PrReviewStats stats={stats} statusFilter={status} />
              <PrReviewList prs={prs} isLoading={isLoading} pageLinks={pageLinks} />
            </Grid>
          </Layout.Main>
        </Layout.Body>
      </Layout.Page>
    </SentryDocumentTitle>
  );
}
