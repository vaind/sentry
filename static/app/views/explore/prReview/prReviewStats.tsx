import {useTheme} from '@emotion/react';
import styled from '@emotion/styled';

import MiniBarChart from 'sentry/components/charts/miniBarChart';
import {ScoreCard} from 'sentry/components/scoreCard';
import {t} from 'sentry/locale';
import {space} from 'sentry/styles/space';
import type {CodeReviewStats} from 'sentry/views/explore/prReview/types';

interface Props {
  stats: CodeReviewStats | undefined;
}

export function PrReviewStats({stats}: Props) {
  const theme = useTheme();

  if (!stats) {
    return null;
  }

  const series = [
    {
      seriesName: t('Reviewed'),
      color: theme.colors.green400,
      data: stats.timeSeries.map(d => ({name: d.date, value: d.reviewed})),
    },
    {
      seriesName: t('Skipped'),
      color: theme.colors.yellow400,
      data: stats.timeSeries.map(d => ({name: d.date, value: d.skipped})),
    },
    {
      seriesName: t('Comments'),
      color: theme.colors.purple400,
      data: stats.timeSeries.map(d => ({name: d.date, value: d.comments})),
    },
  ];

  return (
    <StatsRow>
      <CardsSection>
        <StyledScoreCard
          title={t('Total PRs')}
          score={stats.stats.totalPrs}
          trend={t('%d skipped', stats.stats.skippedPrs)}
        />
        <StyledScoreCard
          title={t('Reviews')}
          score={stats.stats.totalReviews}
          trend={t('%d comments posted', stats.stats.totalComments)}
        />
      </CardsSection>
      <ChartSection>
        <MiniBarChart
          height={96}
          series={series}
          stacked
          isGroupedByDate
          showTimeInTooltip
        />
      </ChartSection>
    </StatsRow>
  );
}

const StatsRow = styled('div')`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: ${space(2)};
`;

const CardsSection = styled('div')`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: ${space(2)};
`;

const ChartSection = styled('div')`
  display: flex;
  align-items: center;
`;

const StyledScoreCard = styled(ScoreCard)`
  margin: 0;
`;
