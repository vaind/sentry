import {Flex} from '@sentry/scraps/layout';
import {Text} from '@sentry/scraps/text';

import {DateTime} from 'sentry/components/dateTime';
import {t} from 'sentry/locale';
import type {TimelineEntry} from 'sentry/views/explore/prReview/types';

interface Props {
  timeline: TimelineEntry[];
}

function formatStage(stage: string): string {
  return stage.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
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
            {formatStage(entry.stage)}
          </Text>
          <Text variant="muted" size="sm">
            <DateTime date={entry.timestamp} seconds />
          </Text>
        </Flex>
      ))}
    </Flex>
  );
}
