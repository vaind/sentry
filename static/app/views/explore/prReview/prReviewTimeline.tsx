import {Flex} from '@sentry/scraps/layout';
import {Text} from '@sentry/scraps/text';

import {DateTime} from 'sentry/components/dateTime';
import {t} from 'sentry/locale';
import type {TimelineEntry} from 'sentry/views/explore/prReview/types';
import {formatStatus} from 'sentry/views/explore/prReview/utils';

interface Props {
  timeline: TimelineEntry[];
}

export function PrReviewTimeline({timeline}: Props) {
  if (timeline.length === 0) {
    return <Text variant="muted">{t('No timeline data available.')}</Text>;
  }

  return (
    <Flex direction="column" gap="sm">
      {timeline.map((entry, index) => (
        <Flex key={index} gap="md" align="center">
          <Text bold size="sm" style={{minWidth: 160}}>
            {formatStatus(entry.stage)}
          </Text>
          <Text variant="muted" size="sm">
            <DateTime date={entry.timestamp} seconds />
          </Text>
        </Flex>
      ))}
    </Flex>
  );
}
