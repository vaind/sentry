import {Fragment} from 'react';
import {useTheme} from '@emotion/react';
import styled from '@emotion/styled';
import {motion, Variants} from 'framer-motion';
import {PlatformIcon} from 'platformicons';

import Placeholder from 'sentry/components/placeholder';
import {PlatformKey} from 'sentry/data/platformCategories';
import platforms from 'sentry/data/platforms';
import {IconCheckmark} from 'sentry/icons';
import {t} from 'sentry/locale';
import pulsingIndicatorStyles from 'sentry/styles/pulsingIndicator';
import space from 'sentry/styles/space';
import {Project} from 'sentry/types';
import testableTransition from 'sentry/utils/testableTransition';

import {useHeartbeat} from './heartbeatFooter/useHeartbeat';

type Props = {
  activeProject: Project | null;
  checkProjectHasFirstEvent: (project: Project) => boolean;
  hasHeartbeatFooter: boolean;
  projects: Project[];
  selectProject: (newProjectId: string) => void;
  // A map from selected platform keys to the projects created by onboarding.
  selectedPlatformToProjectIdMap: {[key in PlatformKey]?: string};
};

function NewProjectSideBarSection({
  project,
  isActive,
  platformOnCreate,
  onClick,
}: {
  isActive: boolean;
  onClick: (projectId: Project['id']) => void;
  platformOnCreate: string;
  project?: Project;
}) {
  const theme = useTheme();
  const {
    firstErrorReceived,
    hasSession,
    firstTransactionReceived,
    eventLoading,
    sessionLoading,
  } = useHeartbeat({project});

  const loading = eventLoading || sessionLoading;
  const serverConnected = hasSession || firstTransactionReceived;

  const platform = project ? project.platform || 'other' : platformOnCreate;
  const platformName = platforms.find(p => p.id === platform)?.name ?? '';

  return (
    <ProjectWrapper
      isActive={loading ? false : isActive}
      onClick={() => project && onClick(project.id)}
      disabled={!project}
    >
      <StyledPlatformIcon platform={platform} size={36} />
      <MiddleWrapper>
        <NameWrapper>{platformName}</NameWrapper>
        {loading ? (
          <Placeholder height="20px" />
        ) : !project ? (
          <Beat color={theme.pink400}>{t('Project deleted')}</Beat>
        ) : firstErrorReceived ? (
          <Beat color={theme.successText}>{t('DSN and error received')}</Beat>
        ) : serverConnected ? (
          <Beat color={theme.pink400}>{t('Awaiting first error')}</Beat>
        ) : (
          <Beat color={theme.pink400}>{t('Awaiting DSN response')}</Beat>
        )}
      </MiddleWrapper>
      {firstErrorReceived ? (
        <StyledIconCheckmark isCircled color="green400" />
      ) : (
        isActive && !loading && <WaitingIndicator />
      )}
    </ProjectWrapper>
  );
}

function ProjectSidebarSection({
  projects,
  activeProject,
  selectProject,
  checkProjectHasFirstEvent,
  selectedPlatformToProjectIdMap,
  hasHeartbeatFooter,
}: Props) {
  const oneProject = (platformOnCreate: string, projectSlug: string) => {
    const project = projects.find(p => p.slug === projectSlug);
    const platform = project ? project.platform || 'other' : platformOnCreate;
    const platformName = platforms.find(p => p.id === platform)?.name ?? '';
    const isActive = !!project && activeProject?.id === project.id;
    const errorReceived = !!project && checkProjectHasFirstEvent(project);
    return (
      <ProjectWrapper
        key={projectSlug}
        isActive={isActive}
        onClick={() => project && selectProject(project.id)}
        disabled={!project}
      >
        <StyledPlatformIcon platform={platform} size={36} />
        <MiddleWrapper>
          <NameWrapper>{platformName}</NameWrapper>
          <SubHeader errorReceived={errorReceived} data-test-id="sidebar-error-indicator">
            {!project
              ? t('Project Deleted')
              : errorReceived
              ? t('Error Received')
              : t('Waiting for error')}
          </SubHeader>
        </MiddleWrapper>
        {errorReceived ? (
          <StyledIconCheckmark isCircled color="green400" />
        ) : (
          isActive && <WaitingIndicator />
        )}
      </ProjectWrapper>
    );
  };
  return (
    <Fragment>
      <Title>{t('Projects to Setup')}</Title>
      {Object.entries(selectedPlatformToProjectIdMap).map(
        ([platformOnCreate, projectSlug]) => {
          if (hasHeartbeatFooter) {
            const project = projects.find(p => p.slug === projectSlug);
            const isActive = !!project && activeProject?.id === project.id;
            return (
              <NewProjectSideBarSection
                key={projectSlug}
                isActive={isActive}
                project={project}
                onClick={selectProject}
                platformOnCreate={platformOnCreate}
              />
            );
          }
          return oneProject(platformOnCreate, projectSlug);
        }
      )}
    </Fragment>
  );
}

export default ProjectSidebarSection;

const Title = styled('span')`
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  margin-left: ${space(2)};
`;

const SubHeader = styled('div')<{errorReceived: boolean}>`
  color: ${p => (p.errorReceived ? p.theme.successText : p.theme.pink400)};
`;

const StyledPlatformIcon = styled(PlatformIcon)``;

const ProjectWrapper = styled('div')<{disabled: boolean; isActive: boolean}>`
  display: flex;
  flex-direction: row;
  align-items: center;
  background-color: ${p => p.isActive && p.theme.gray100};
  padding: ${space(2)};
  cursor: pointer;
  border-radius: 4px;
  user-select: none;
  ${p =>
    p.disabled &&
    `
    cursor: not-allowed;
    ${StyledPlatformIcon} {
      filter: grayscale(1);
    }
    ${SubHeader} {
      color: ${p.theme.gray400};
    }
    ${Beat} {
      color: ${p.theme.gray400};
    }
    ${NameWrapper} {
      text-decoration-line: line-through;
    }
  `}
`;

const indicatorAnimation: Variants = {
  initial: {opacity: 0, y: -10},
  animate: {opacity: 1, y: 0},
  exit: {opacity: 0, y: 10},
};

const WaitingIndicator = styled(motion.div)`
  margin: 0 6px;
  flex-shrink: 0;
  ${pulsingIndicatorStyles};
  background-color: ${p => p.theme.pink300};
`;
const StyledIconCheckmark = styled(IconCheckmark)`
  flex-shrink: 0;
`;

WaitingIndicator.defaultProps = {
  variants: indicatorAnimation,
  transition: testableTransition(),
};

const MiddleWrapper = styled('div')`
  margin: 0 ${space(1)};
  flex-grow: 1;
  overflow: hidden;
`;

const NameWrapper = styled('div')`
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
`;

const Beat = styled('div')<{color: string}>`
  color: ${p => p.color};
`;
