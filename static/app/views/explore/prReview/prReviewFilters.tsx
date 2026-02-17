import {CompactSelect} from '@sentry/scraps/compactSelect';
import {Flex} from '@sentry/scraps/layout';

import {t} from 'sentry/locale';

interface Props {
  onStatusChange: (status: string) => void;
  onTriggerTypeChange: (triggerType: string) => void;
  status: string;
  triggerType: string;
}

const STATUS_OPTIONS = [
  {value: '', label: t('All Statuses')},
  {value: 'webhook_received', label: t('Webhook Received')},
  {value: 'preflight_denied', label: t('Preflight Denied')},
  {value: 'webhook_filtered', label: t('Filtered')},
  {value: 'task_enqueued', label: t('Task Enqueued')},
  {value: 'sent_to_seer', label: t('Sent to Seer')},
  {value: 'review_started', label: t('Review Started')},
  {value: 'review_completed', label: t('Review Completed')},
  {value: 'review_failed', label: t('Review Failed')},
];

const TRIGGER_OPTIONS = [
  {value: '', label: t('All Triggers')},
  {value: 'on_ready_for_review', label: t('Ready for Review')},
  {value: 'on_new_commit', label: t('New Commit')},
  {value: 'on_command_phrase', label: t('Command Phrase')},
];

export function PrReviewFilters({
  status,
  triggerType,
  onStatusChange,
  onTriggerTypeChange,
}: Props) {
  return (
    <Flex gap="md">
      <CompactSelect
        triggerProps={{prefix: t('Status')}}
        value={status}
        options={STATUS_OPTIONS}
        onChange={opt => onStatusChange(opt.value)}
      />
      <CompactSelect
        triggerProps={{prefix: t('Trigger')}}
        value={triggerType}
        options={TRIGGER_OPTIONS}
        onChange={opt => onTriggerTypeChange(opt.value)}
      />
    </Flex>
  );
}
