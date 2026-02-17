import {useState} from 'react';

import * as Layout from 'sentry/components/layouts/thirds';
import SentryDocumentTitle from 'sentry/components/sentryDocumentTitle';
import {t} from 'sentry/locale';
import {useApiQuery} from 'sentry/utils/queryClient';
import useOrganization from 'sentry/utils/useOrganization';
import {PrReviewFilters} from 'sentry/views/explore/prReview/prReviewFilters';
import {PrReviewList} from 'sentry/views/explore/prReview/prReviewList';
import {PrReviewStats} from 'sentry/views/explore/prReview/prReviewStats';
import type {
  CodeReviewEvent,
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
    data: events,
    isLoading,
    getResponseHeader,
  } = useApiQuery<CodeReviewEvent[]>(
    [`/organizations/${organization.slug}/code-review-events/`, {query: queryParams}],
    {staleTime: 30_000}
  );

  const {data: stats} = useApiQuery<CodeReviewStatsType>(
    [`/organizations/${organization.slug}/code-review-stats/`],
    {staleTime: 60_000}
  );

  const pageLinks = getResponseHeader?.('Link') ?? null;

  return (
    <SentryDocumentTitle title={t('PR Reviews')} orgSlug={organization.slug}>
      <Layout.Page>
        <Layout.Header>
          <Layout.HeaderContent>
            <Layout.Title>{t('PR Reviews')}</Layout.Title>
          </Layout.HeaderContent>
        </Layout.Header>
        <Layout.Body>
          <Layout.Main width="full">
            <PrReviewStats stats={stats?.stats} />
            <PrReviewFilters
              status={status}
              triggerType={triggerType}
              onStatusChange={setStatus}
              onTriggerTypeChange={setTriggerType}
            />
            <PrReviewList events={events} isLoading={isLoading} pageLinks={pageLinks} />
          </Layout.Main>
        </Layout.Body>
      </Layout.Page>
    </SentryDocumentTitle>
  );
}
