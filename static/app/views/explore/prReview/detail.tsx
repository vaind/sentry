import {Fragment} from 'react';

import {Tag} from '@sentry/scraps/badge';
import {Flex} from '@sentry/scraps/layout';
import {ExternalLink} from '@sentry/scraps/link';
import {Heading, Text} from '@sentry/scraps/text';

import {DateTime} from 'sentry/components/dateTime';
import * as Layout from 'sentry/components/layouts/thirds';
import LoadingIndicator from 'sentry/components/loadingIndicator';
import {PanelTable} from 'sentry/components/panels/panelTable';
import SentryDocumentTitle from 'sentry/components/sentryDocumentTitle';
import {t} from 'sentry/locale';
import {useApiQuery} from 'sentry/utils/queryClient';
import useOrganization from 'sentry/utils/useOrganization';
import {useParams} from 'sentry/utils/useParams';
import type {CodeReviewPRDetails} from 'sentry/views/explore/prReview/types';
import {formatStatus, statusToTagVariant} from 'sentry/views/explore/prReview/utils';

export default function PrReviewDetail() {
  const organization = useOrganization();
  const {repoId, prNumber} = useParams<{prNumber: string; repoId: string}>();

  const {data: pr, isLoading} = useApiQuery<CodeReviewPRDetails>(
    [`/organizations/${organization.slug}/code-review-prs/${repoId}/${prNumber}/`],
    {staleTime: 30_000}
  );

  if (isLoading) {
    return <LoadingIndicator />;
  }

  if (!pr) {
    return null;
  }

  const title = pr.prTitle ? `PR #${pr.prNumber}: ${pr.prTitle}` : `PR #${pr.prNumber}`;

  return (
    <SentryDocumentTitle title={title} orgSlug={organization.slug}>
      <Layout.Page>
        <Layout.Header>
          <Layout.HeaderContent>
            <Layout.Title>
              {title}
              {pr.prUrl ? (
                <Fragment>
                  {' '}
                  <ExternalLink href={pr.prUrl}>{t('View on GitHub')}</ExternalLink>
                </Fragment>
              ) : null}
            </Layout.Title>
          </Layout.HeaderContent>
        </Layout.Header>
        <Layout.Body>
          <Layout.Main width="full">
            <Flex direction="column" gap="lg">
              <Flex direction="column" gap="sm">
                <Heading as="h3">{t('PR Details')}</Heading>
                <DetailRow label={t('Repository')}>
                  {pr.repositoryName ?? pr.repositoryId}
                </DetailRow>
                <DetailRow label={t('Author')}>{pr.prAuthor ?? '—'}</DetailRow>
              </Flex>

              <Flex direction="column" gap="sm">
                <Heading as="h3">{t('Review Events')}</Heading>
                <PanelTable
                  headers={[t('Trigger'), t('Status'), t('Time'), t('Comments')]}
                  isEmpty={pr.events.length === 0}
                  emptyMessage={t('No review events found.')}
                >
                  {pr.events.map(event => (
                    <Fragment key={event.id}>
                      <div>{event.trigger ? formatStatus(event.trigger) : '—'}</div>
                      <div>
                        <Tag variant={statusToTagVariant(event.status)}>
                          {formatStatus(event.status)}
                        </Tag>
                      </div>
                      <div>
                        <DateTime date={event.triggerAt ?? event.dateAdded} seconds />
                      </div>
                      <div>{event.commentsPosted ?? '—'}</div>
                    </Fragment>
                  ))}
                </PanelTable>
              </Flex>

              {pr.comments.length > 0 && (
                <Flex direction="column" gap="sm">
                  <Heading as="h3">{t('Comments')}</Heading>
                  {pr.comments.map((comment, index) => (
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

              {pr.commentsError && (
                <Text variant="muted">{t('Unable to load comments from Seer.')}</Text>
              )}
            </Flex>
          </Layout.Main>
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
