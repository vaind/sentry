import type {Tag} from '@sentry/scraps/badge';

/**
 * Maps a code review event status to a Tag color type for visual differentiation.
 */
export function statusToTagType(
  status: string
): React.ComponentProps<typeof Tag>['type'] {
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

/**
 * Converts a snake_case status string to Title Case for display.
 */
export function formatStatus(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
