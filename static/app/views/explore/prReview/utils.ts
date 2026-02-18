import getDuration from 'sentry/utils/duration/getDuration';
import {toTitleCase} from 'sentry/utils/string/toTitleCase';
import type {TagVariant} from 'sentry/utils/theme/types';

export function statusToTagVariant(status: string): TagVariant {
  switch (status) {
    case 'review_completed':
      return 'success';
    case 'review_failed':
      return 'danger';
    case 'preflight_denied':
    case 'webhook_filtered':
      return 'warning';
    case 'sent_to_seer':
    case 'review_started':
      return 'info';
    default:
      return 'muted';
  }
}

export function prStateToTagVariant(state: string | null): TagVariant {
  switch (state) {
    case 'open':
      return 'success';
    case 'merged':
      return 'info';
    case 'closed':
      return 'danger';
    default:
      return 'muted';
  }
}

export function formatStatus(status: string): string {
  return toTitleCase(status.replace(/_/g, ' '));
}

export function formatDurationMs(ms: number): string {
  return getDuration(ms / 1000, 0, false, true);
}
