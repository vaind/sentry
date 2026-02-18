import {CompactSelect} from '@sentry/scraps/compactSelect';
import {Flex} from '@sentry/scraps/layout';
import {OverlayTrigger} from '@sentry/scraps/overlayTrigger';

import {t} from 'sentry/locale';
import type {CodeReviewRepository} from 'sentry/views/explore/prReview/types';

interface Props {
  onRepositoryChange: (repositoryIds: string[]) => void;
  onStatusChange: (status: string) => void;
  repositories: CodeReviewRepository[];
  repositoryIds: string[];
  status: string;
}

const STATUS_OPTIONS = [
  {value: '', label: t('All Statuses')},
  {value: 'open', label: t('Open')},
  {value: 'merged', label: t('Merged')},
  {value: 'closed', label: t('Closed')},
];

export function PrReviewFilters({
  status,
  repositoryIds,
  repositories,
  onStatusChange,
  onRepositoryChange,
}: Props) {
  const repoOptions = repositories.map(repo => ({
    value: repo.id,
    label: repo.name,
    textValue: repo.name,
  }));

  return (
    <Flex gap="md">
      <CompactSelect
        trigger={triggerProps => (
          <OverlayTrigger.Button {...triggerProps} prefix={t('Status')} />
        )}
        value={status}
        options={STATUS_OPTIONS}
        onChange={opt => onStatusChange(opt.value)}
      />
      <CompactSelect
        multiple
        searchable
        searchPlaceholder={t('Search repositories...')}
        trigger={triggerProps => (
          <OverlayTrigger.Button {...triggerProps} prefix={t('Repository')} />
        )}
        value={repositoryIds}
        options={repoOptions}
        onChange={opts => onRepositoryChange(opts.map(o => o.value))}
      />
    </Flex>
  );
}
