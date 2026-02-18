import type React from 'react';
import {Fragment} from 'react';

import {Tag} from '@sentry/scraps/badge';
import {ExternalLink, Link} from '@sentry/scraps/link';

import LoadingIndicator from 'sentry/components/loadingIndicator';
import Pagination from 'sentry/components/pagination';
import {PanelTable} from 'sentry/components/panels/panelTable';
import TimeSince from 'sentry/components/timeSince';
import {IconOpen} from 'sentry/icons';
import {t} from 'sentry/locale';
import useOrganization from 'sentry/utils/useOrganization';
import type {CodeReviewPR} from 'sentry/views/explore/prReview/types';
import {
  formatStatus,
  prStateToTagVariant,
  statusToTagVariant,
} from 'sentry/views/explore/prReview/utils';

interface Props {
  isLoading: boolean;
  pageLinks: string | null;
  paginationCaption: React.ReactNode;
  prs: CodeReviewPR[] | undefined;
}

export function PrReviewList({prs, isLoading, pageLinks, paginationCaption}: Props) {
  const organization = useOrganization();

  if (isLoading) {
    return <LoadingIndicator />;
  }

  return (
    <Fragment>
      <PanelTable
        headers={[
          t('Repository'),
          t('PR #'),
          t('Title'),
          t('Author'),
          t('PR Status'),
          t('Review Status'),
          t('Reviews'),
          t('Comments'),
          t('Last Activity'),
        ]}
        isEmpty={!prs || prs.length === 0}
        emptyMessage={t('No pull requests found.')}
      >
        {prs?.map(pr => (
          <Fragment key={`${pr.repositoryId}-${pr.prNumber}`}>
            <div>{pr.repositoryName ?? pr.repositoryId}</div>
            <div>
              {pr.prUrl ? (
                <ExternalLink href={pr.prUrl}>
                  #{pr.prNumber} <IconOpen size="xs" />
                </ExternalLink>
              ) : (
                `#${pr.prNumber}`
              )}
            </div>
            <div>
              <Link
                to={`/organizations/${organization.slug}/explore/pr-review/${pr.repositoryId}/${pr.prNumber}/`}
              >
                {pr.prTitle ?? t('View details')}
              </Link>
            </div>
            <div>{pr.prAuthor ?? '—'}</div>
            <div>
              {pr.prState ? (
                <Tag variant={prStateToTagVariant(pr.prState)}>
                  {formatStatus(pr.prState)}
                </Tag>
              ) : (
                '—'
              )}
            </div>
            <div>
              <Tag variant={statusToTagVariant(pr.latestStatus)}>
                {formatStatus(pr.latestStatus)}
              </Tag>
            </div>
            <div>{pr.eventCount}</div>
            <div>{pr.totalComments}</div>
            <div>
              <TimeSince date={pr.lastActivity} />
            </div>
          </Fragment>
        ))}
      </PanelTable>
      <Pagination pageLinks={pageLinks} caption={paginationCaption} />
    </Fragment>
  );
}
