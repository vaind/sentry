import {CompactSelect} from '@sentry/scraps/compactSelect';
import {OverlayTrigger} from '@sentry/scraps/overlayTrigger';

import PageFilterBar from 'sentry/components/pageFilters/pageFilterBar';
import {t} from 'sentry/locale';
import type {CodeReviewRepository} from 'sentry/views/explore/prReview/types';

interface Props {
  onRepositoryChange: (repositoryIds: string[]) => void;
  onStatusChange: (status: string) => void;
  onTimeRangeChange: (timeRange: string) => void;
  repositories: CodeReviewRepository[];
  repositoryIds: string[];
  status: string;
  timeRange: string;
}

const STATUS_OPTIONS = [
  {value: '', label: t('All Statuses')},
  {value: 'open', label: t('Open')},
  {value: 'merged', label: t('Merged')},
  {value: 'closed', label: t('Closed')},
];

const TIME_RANGE_OPTIONS = [
  {value: '24h', label: t('24H')},
  {value: '7d', label: t('7D')},
  {value: '14d', label: t('14D')},
  {value: '30d', label: t('30D')},
  {value: '90d', label: t('90D')},
];

function getRepoTriggerLabel(
  repositoryIds: string[],
  repositories: CodeReviewRepository[]
): string {
  if (repositoryIds.length === 0) {
    return t('All Repositories');
  }
  const firstId = repositoryIds[0]!;
  const selected = repositories.find(r => r.id === firstId);
  const label = selected?.name ?? firstId;
  if (repositoryIds.length === 1) {
    return label;
  }
  return `${label} (+${repositoryIds.length - 1})`;
}

export function PrReviewFilters({
  status,
  repositoryIds,
  repositories,
  timeRange,
  onStatusChange,
  onRepositoryChange,
  onTimeRangeChange,
}: Props) {
  const repoOptions = repositories.map(repo => ({
    value: repo.id,
    label: repo.name,
    textValue: repo.name,
  }));

  return (
    <PageFilterBar condensed>
      <CompactSelect
        multiple
        searchable
        searchPlaceholder={t('Search...')}
        trigger={triggerProps => (
          <OverlayTrigger.Button {...triggerProps}>
            {getRepoTriggerLabel(repositoryIds, repositories)}
          </OverlayTrigger.Button>
        )}
        value={repositoryIds}
        options={repoOptions}
        onChange={opts => onRepositoryChange(opts.map(o => o.value))}
      />
      <CompactSelect
        trigger={triggerProps => (
          <OverlayTrigger.Button {...triggerProps}>
            {STATUS_OPTIONS.find(o => o.value === status)?.label ?? t('All Statuses')}
          </OverlayTrigger.Button>
        )}
        value={status}
        options={STATUS_OPTIONS}
        onChange={opt => onStatusChange(opt.value)}
      />
      <CompactSelect
        trigger={triggerProps => (
          <OverlayTrigger.Button {...triggerProps}>
            {TIME_RANGE_OPTIONS.find(o => o.value === timeRange)?.label ?? timeRange}
          </OverlayTrigger.Button>
        )}
        value={timeRange}
        options={TIME_RANGE_OPTIONS}
        onChange={opt => onTimeRangeChange(opt.value)}
      />
    </PageFilterBar>
  );
}
