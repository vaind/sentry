import type {TagVariant} from 'sentry/utils/theme/types';

/**
 * Maps a code review event status to a Tag variant for visual differentiation.
 */
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

/**
 * Converts a snake_case status string to Title Case for display.
 */
export function formatStatus(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
