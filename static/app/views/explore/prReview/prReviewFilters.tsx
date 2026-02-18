import {CompactSelect} from '@sentry/scraps/compactSelect';
import {Flex} from '@sentry/scraps/layout';
import {OverlayTrigger} from '@sentry/scraps/overlayTrigger';

import {t} from 'sentry/locale';

interface Props {
  onStatusChange: (status: string) => void;
  onTriggerTypeChange: (triggerType: string) => void;
  status: string;
  triggerType: string;
}

const STATUS_OPTIONS = [
  {value: '', label: t('All Statuses')},
  {value: 'open', label: t('Open')},
  {value: 'merged', label: t('Merged')},
  {value: 'closed', label: t('Closed')},
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
        trigger={triggerProps => (
          <OverlayTrigger.Button {...triggerProps} prefix={t('Status')} />
        )}
        value={status}
        options={STATUS_OPTIONS}
        onChange={opt => onStatusChange(opt.value)}
      />
      <CompactSelect
        trigger={triggerProps => (
          <OverlayTrigger.Button {...triggerProps} prefix={t('Trigger')} />
        )}
        value={triggerType}
        options={TRIGGER_OPTIONS}
        onChange={opt => onTriggerTypeChange(opt.value)}
      />
    </Flex>
  );
}
