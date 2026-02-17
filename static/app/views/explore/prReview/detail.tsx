import {Tag} from '@sentry/scraps/badge';
import {Flex} from '@sentry/scraps/layout';
import {ExternalLink} from '@sentry/scraps/link';
import {Heading, Text} from '@sentry/scraps/text';

import {DateTime} from 'sentry/components/dateTime';
import * as Layout from 'sentry/components/layouts/thirds';
import LoadingIndicator from 'sentry/components/loadingIndicator';
import SentryDocumentTitle from 'sentry/components/sentryDocumentTitle';
import {t} from 'sentry/locale';
import {useApiQuery} from 'sentry/utils/queryClient';
import useOrganization from 'sentry/utils/useOrganization';
import {useParams} from 'sentry/utils/useParams';
import ExploreBreadcrumb from 'sentry/views/explore/components/breadcrumb';
import {PrReviewTimeline} from 'sentry/views/explore/prReview/prReviewTimeline';
import type {CodeReviewEvent} from 'sentry/views/explore/prReview/types';
import {formatStatus, statusToTagType} from 'sentry/views/explore/prReview/utils';

export default function PrReviewDetail() {
  const organization = useOrganization();
  const {eventId} = useParams<{eventId: string}>();

  const {data: event, isLoading} = useApiQuery<CodeReviewEvent>(
    [`/organizations/${organization.slug}/code-review-events/${eventId}/`],
    {staleTime: 30_000}
  );

  if (isLoading) {
    return <LoadingIndicator />;
  }

  if (!event) {
    return null;
  }

  const title = event.prTitle
    ? `PR #${event.prNumber}: ${event.prTitle}`
    : `PR Review ${eventId}`;

  return (
    <SentryDocumentTitle title={title} orgSlug={organization.slug}>
      <Layout.Page>
        <Layout.Header>
          <Layout.HeaderContent>
            <ExploreBreadcrumb />
            <Layout.Title>{title}</Layout.Title>
          </Layout.HeaderContent>
        </Layout.Header>
        <Layout.Body>
          <Layout.Main>
            <Flex direction="column" gap="lg">
              <Flex direction="column" gap="sm">
                <Heading as="h3">{t('Details')}</Heading>
                <DetailRow label={t('Repository')}>
                  {event.repositoryName ?? event.repositoryId}
                </DetailRow>
                <DetailRow label={t('PR')}>
                  {event.prUrl ? (
                    <ExternalLink href={event.prUrl}>#{event.prNumber}</ExternalLink>
                  ) : (
                    `#${event.prNumber ?? '—'}`
                  )}
                </DetailRow>
                <DetailRow label={t('Author')}>{event.prAuthor ?? '—'}</DetailRow>
                <DetailRow label={t('Status')}>
                  <Tag type={statusToTagType(event.status)}>
                    {formatStatus(event.status)}
                  </Tag>
                </DetailRow>
                <DetailRow label={t('Trigger')}>
                  {event.trigger ? formatStatus(event.trigger) : '—'}
                </DetailRow>
                <DetailRow label={t('Triggered by')}>
                  {event.triggerUser ?? '—'}
                </DetailRow>
                <DetailRow label={t('Date')}>
                  <DateTime date={event.dateAdded} seconds />
                </DetailRow>
                <DetailRow label={t('Comments Posted')}>
                  {event.commentsPosted ?? '—'}
                </DetailRow>
                {event.denialReason && (
                  <DetailRow label={t('Denial Reason')}>{event.denialReason}</DetailRow>
                )}
                {event.seerRunId && (
                  <DetailRow label={t('Seer Run ID')}>{event.seerRunId}</DetailRow>
                )}
              </Flex>

              {event.timeline && event.timeline.length > 0 && (
                <Flex direction="column" gap="sm">
                  <Heading as="h3">{t('Timeline')}</Heading>
                  <PrReviewTimeline timeline={event.timeline} />
                </Flex>
              )}

              {event.comments && event.comments.length > 0 && (
                <Flex direction="column" gap="sm">
                  <Heading as="h3">{t('Comments')}</Heading>
                  {event.comments.map((comment, index) => (
                    <Flex key={index} direction="column" gap="xs" padding="md">
                      {comment.file && (
                        <Text size="sm" bold>
                          {comment.file}
                          {comment.line ? `:${comment.line}` : ''}
                        </Text>
                      )}
                      {comment.severity && (
                        <Text variant="muted" size="sm">
                          {comment.severity}
                        </Text>
                      )}
                      <Text>{comment.body}</Text>
                    </Flex>
                  ))}
                </Flex>
              )}

              {event.commentsError && (
                <Text variant="muted">{t('Unable to load comments from Seer.')}</Text>
              )}
            </Flex>
          </Layout.Main>
          <Layout.Side>
            <Flex direction="column" gap="sm">
              <Heading as="h4">{t('Metadata')}</Heading>
              <Text variant="muted" size="sm">
                {t('Event Type')}: {event.githubEventType}
              </Text>
              <Text variant="muted" size="sm">
                {t('Action')}: {event.githubEventAction}
              </Text>
              {event.githubDeliveryId && (
                <Text variant="muted" size="sm">
                  {t('Delivery ID')}: {event.githubDeliveryId}
                </Text>
              )}
              {event.targetCommitSha && (
                <Text variant="muted" size="sm">
                  {t('Commit')}: {event.targetCommitSha.slice(0, 8)}
                </Text>
              )}
            </Flex>
          </Layout.Side>
        </Layout.Body>
      </Layout.Page>
    </SentryDocumentTitle>
  );
}

function DetailRow({label, children}: {children: React.ReactNode; label: string}) {
  return (
    <Flex gap="md" align="center">
      <Text bold size="sm" style={{minWidth: 140}}>
        {label}
      </Text>
      {children}
    </Flex>
  );
}
