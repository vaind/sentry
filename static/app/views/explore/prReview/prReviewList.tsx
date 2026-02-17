import {Fragment} from 'react';

import {Tag} from '@sentry/scraps/badge';
import {ExternalLink, Link} from '@sentry/scraps/link';

import {DateTime} from 'sentry/components/dateTime';
import LoadingIndicator from 'sentry/components/loadingIndicator';
import Pagination from 'sentry/components/pagination';
import {PanelTable} from 'sentry/components/panels/panelTable';
import {t} from 'sentry/locale';
import useOrganization from 'sentry/utils/useOrganization';
import type {CodeReviewEvent} from 'sentry/views/explore/prReview/types';

interface Props {
  events: CodeReviewEvent[] | undefined;
  isLoading: boolean;
  pageLinks: string | null;
}

function statusToTagType(status: string): React.ComponentProps<typeof Tag>['type'] {
  switch (status) {
    case 'review_completed':
      return 'success';
    case 'review_failed':
      return 'error';
    case 'preflight_denied':
    case 'webhook_filtered':
      return 'warning';
    case 'sent_to_seer':
    case 'review_started':
      return 'info';
    default:
      return 'default';
  }
}

function formatStatus(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

export function PrReviewList({events, isLoading, pageLinks}: Props) {
  const organization = useOrganization();

  if (isLoading) {
    return <LoadingIndicator />;
  }

  return (
    <Fragment>
      <PanelTable
        headers={[
          t('Repository'),
          t('PR'),
          t('Trigger'),
          t('Status'),
          t('Time'),
          t('Comments'),
        ]}
        isEmpty={!events || events.length === 0}
        emptyMessage={t('No code review events found.')}
      >
        {events?.map(event => (
          <Fragment key={event.id}>
            <div>{event.repositoryName ?? event.repositoryId}</div>
            <div>
              {event.prUrl ? (
                <ExternalLink href={event.prUrl}>#{event.prNumber}</ExternalLink>
              ) : (
                `#${event.prNumber ?? '—'}`
              )}{' '}
              <Link
                to={`/organizations/${organization.slug}/explore/pr-review/${event.id}/`}
              >
                {event.prTitle ?? t('View details')}
              </Link>
            </div>
            <div>{event.trigger ? formatStatus(event.trigger) : '—'}</div>
            <div>
              <Tag type={statusToTagType(event.status)}>{formatStatus(event.status)}</Tag>
            </div>
            <div>
              <DateTime date={event.dateAdded} />
            </div>
            <div>{event.commentsPosted ?? '—'}</div>
          </Fragment>
        ))}
      </PanelTable>
      <Pagination pageLinks={pageLinks} />
    </Fragment>
  );
}
