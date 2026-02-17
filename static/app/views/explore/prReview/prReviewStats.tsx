import {Flex} from '@sentry/scraps/layout';
import {Heading, Text} from '@sentry/scraps/text';

import {t} from 'sentry/locale';
import type {CodeReviewStats} from 'sentry/views/explore/prReview/types';

interface Props {
  stats: CodeReviewStats['stats'] | undefined;
}

function StatCard({label, value}: {label: string; value: number | string}) {
  return (
    <Flex direction="column" gap="xs" padding="md" style={{minWidth: 120}}>
      <Text variant="muted" size="sm">
        {label}
      </Text>
      <Heading as="h3">{value}</Heading>
    </Flex>
  );
}

export function PrReviewStats({stats}: Props) {
  if (!stats) {
    return null;
  }

  return (
    <Flex gap="lg" wrap="wrap">
      <StatCard label={t('Total Reviews')} value={stats.total} />
      <StatCard label={t('Completed')} value={stats.completed} />
      <StatCard label={t('Failed')} value={stats.failed} />
      <StatCard label={t('Preflight Denied')} value={stats.preflightDenied} />
      <StatCard label={t('Filtered')} value={stats.webhookFiltered} />
      <StatCard label={t('Comments Posted')} value={stats.totalComments} />
    </Flex>
  );
}
