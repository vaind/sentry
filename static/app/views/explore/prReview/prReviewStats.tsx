import styled from '@emotion/styled';

import {ScoreCard} from 'sentry/components/scoreCard';
import {t} from 'sentry/locale';
import {space} from 'sentry/styles/space';
import type {CodeReviewStats} from 'sentry/views/explore/prReview/types';

interface Props {
  stats: CodeReviewStats['stats'] | undefined;
}

export function PrReviewStats({stats}: Props) {
  if (!stats) {
    return null;
  }

  return (
    <StatsGrid>
      <StyledScoreCard title={t('Total Reviews')} score={stats.total} />
      <StyledScoreCard title={t('Completed')} score={stats.completed} />
      <StyledScoreCard title={t('Failed')} score={stats.failed} />
      <StyledScoreCard title={t('Preflight Denied')} score={stats.preflightDenied} />
      <StyledScoreCard title={t('Filtered')} score={stats.webhookFiltered} />
      <StyledScoreCard title={t('Comments Posted')} score={stats.totalComments} />
    </StatsGrid>
  );
}

const StatsGrid = styled('div')`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: ${space(2)};

  @media (min-width: ${p => p.theme.breakpoints.sm}) {
    grid-template-columns: repeat(3, 1fr);
  }
  @media (min-width: ${p => p.theme.breakpoints.lg}) {
    grid-template-columns: repeat(6, 1fr);
  }
`;

const StyledScoreCard = styled(ScoreCard)`
  margin: 0;
`;
