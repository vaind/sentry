import {useEffect} from 'react';
import {RouteComponentProps} from 'react-router';

import {fetchProjectDetails} from 'sentry/actionCreators/project';
import {analytics} from 'sentry/utils/analytics';
import useApi from 'sentry/utils/useApi';
import useOrganization from 'sentry/utils/useOrganization';
import usePageFilters from 'sentry/utils/usePageFilters';
import useProjects from 'sentry/utils/useProjects';

import GroupDetails from './groupDetails';

type Props = {
  children: React.ReactNode;
} & RouteComponentProps<{groupId: string; orgId: string}, {}>;

function OrganizationGroupDetails(props: Props) {
  const {isReady, selection} = usePageFilters();
  const organization = useOrganization();
  const {projects} = useProjects();
  const api = useApi();

  const {params, location} = props;

  const projectId = location.query.project;
  const project = projects.find(proj => proj.id === projectId);

  useEffect(() => {
    if (!project?.slug) {
      return;
    }

    fetchProjectDetails({api, orgSlug: organization.slug, projSlug: project.slug});
  }, [api, organization.slug, project?.slug]);

  useEffect(() => {
    analytics('issue_page.viewed', {
      group_id: parseInt(params.groupId, 10),
      org_id: parseInt(organization.id, 10),
    });
  }, [organization, params.groupId]);

  return (
    <GroupDetails
      key={`${params.groupId}-envs:${selection.environments.join(',')}`}
      environments={selection.environments}
      organization={organization}
      projects={projects}
      isGlobalSelectionReady={isReady}
      {...props}
    />
  );
}

export default OrganizationGroupDetails;
