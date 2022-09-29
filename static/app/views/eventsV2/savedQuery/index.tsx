import {Fragment, PureComponent} from 'react';
import {browserHistory, InjectedRouter} from 'react-router';
import {useTheme} from '@emotion/react';
import styled from '@emotion/styled';
import {FocusScope} from '@react-aria/focus';
import {AnimatePresence} from 'framer-motion';
import {Location} from 'history';
import isEqual from 'lodash/isEqual';

import {Client} from 'sentry/api';
import Feature from 'sentry/components/acl/feature';
import FeatureDisabled from 'sentry/components/acl/featureDisabled';
import GuideAnchor from 'sentry/components/assistant/guideAnchor';
import Banner from 'sentry/components/banner';
import Button from 'sentry/components/button';
import ButtonBar from 'sentry/components/buttonBar';
import {CreateAlertFromViewButton} from 'sentry/components/createAlertButton';
import {Hovercard} from 'sentry/components/hovercard';
import InputControl from 'sentry/components/input';
import {Overlay, PositionWrapper} from 'sentry/components/overlay';
import {IconDelete, IconStar} from 'sentry/icons';
import {t} from 'sentry/locale';
import space from 'sentry/styles/space';
import {Organization, Project, SavedQuery} from 'sentry/types';
import {trackAnalyticsEvent} from 'sentry/utils/analytics';
import EventView from 'sentry/utils/discover/eventView';
import {getDiscoverQueriesUrl} from 'sentry/utils/discover/urls';
import useOverlay from 'sentry/utils/useOverlay';
import withApi from 'sentry/utils/withApi';
import withProjects from 'sentry/utils/withProjects';
import {handleAddQueryToDashboard} from 'sentry/views/eventsV2/utils';

import {
  handleCreateQuery,
  handleDeleteQuery,
  handleUpdateHomepageQuery,
  handleUpdateQuery,
} from './utils';

type SaveAsDropdownProps = {
  disabled: boolean;
  modifiedHandleCreateQuery: (e: React.MouseEvent<Element>) => void;
  onChangeInput: (e: React.FormEvent<HTMLInputElement>) => void;
  queryName: string;
};

function SaveAsDropdown({
  queryName,
  disabled,
  onChangeInput,
  modifiedHandleCreateQuery,
}: SaveAsDropdownProps) {
  const {isOpen, triggerProps, overlayProps, arrowProps} = useOverlay();
  const theme = useTheme();

  return (
    <div>
      <Button
        {...triggerProps}
        icon={<IconStar />}
        aria-label={t('Save as')}
        disabled={disabled}
      >
        {`${t('Save as')}\u2026`}
      </Button>
      <AnimatePresence>
        {isOpen && (
          <FocusScope contain restoreFocus autoFocus>
            <PositionWrapper zIndex={theme.zIndex.dropdown} {...overlayProps}>
              <StyledOverlay arrowProps={arrowProps} animated>
                <SaveAsInput
                  type="text"
                  name="query_name"
                  placeholder={t('Display name')}
                  value={queryName || ''}
                  onChange={onChangeInput}
                  disabled={disabled}
                />
                <SaveAsButton
                  onClick={modifiedHandleCreateQuery}
                  priority="primary"
                  disabled={disabled || !queryName}
                >
                  {t('Save for Org')}
                </SaveAsButton>
              </StyledOverlay>
            </PositionWrapper>
          </FocusScope>
        )}
      </AnimatePresence>
    </div>
  );
}

type DefaultProps = {
  disabled: boolean;
};

type Props = DefaultProps & {
  api: Client;

  eventView: EventView;
  /**
   * DO NOT USE `Location` TO GENERATE `EventView` IN THIS COMPONENT.
   *
   * In this component, state is generated from EventView and SavedQueriesStore.
   * Using Location to rebuild EventView will break the tests. `Location` is
   * passed down only because it is needed for navigation.
   */
  location: Location;
  organization: Organization;
  projects: Project[];
  router: InjectedRouter;
  savedQuery: SavedQuery | undefined;
  savedQueryLoading: boolean;
  setSavedQuery: (savedQuery: SavedQuery) => void;
  updateCallback: () => void;
  yAxis: string[];
};

type State = {
  isEditingQuery: boolean;
  isNewQuery: boolean;

  queryName: string;
};

class SavedQueryButtonGroup extends PureComponent<Props, State> {
  static getDerivedStateFromProps(nextProps: Readonly<Props>, prevState: State): State {
    const {eventView: nextEventView, savedQuery, savedQueryLoading, yAxis} = nextProps;

    // For a new unsaved query
    if (!savedQuery) {
      return {
        isNewQuery: true,
        isEditingQuery: false,
        queryName: prevState.queryName || '',
      };
    }

    if (savedQueryLoading) {
      return prevState;
    }

    const savedEventView = EventView.fromSavedQuery(savedQuery);

    // Switching from a SavedQuery to another SavedQuery
    if (savedEventView.id !== nextEventView.id) {
      return {
        isNewQuery: false,
        isEditingQuery: false,
        queryName: '',
      };
    }

    // For modifying a SavedQuery
    const isEqualQuery = nextEventView.isEqualTo(savedEventView);
    // undefined saved yAxis defaults to count() and string values are converted to array
    const isEqualYAxis = isEqual(
      yAxis,
      !savedQuery.yAxis
        ? ['count()']
        : typeof savedQuery.yAxis === 'string'
        ? [savedQuery.yAxis]
        : savedQuery.yAxis
    );
    return {
      isNewQuery: false,
      isEditingQuery: !isEqualQuery || !isEqualYAxis,

      // HACK(leedongwei): See comment at SavedQueryButtonGroup.onFocusInput
      queryName: prevState.queryName || '',
    };
  }

  /**
   * Stop propagation for the input and container so people can interact with
   * the inputs in the dropdown.
   */
  static stopEventPropagation = (event: React.MouseEvent) => {
    const capturedElements = ['LI', 'INPUT'];

    if (
      event.target instanceof Element &&
      capturedElements.includes(event.target.nodeName)
    ) {
      event.preventDefault();
      event.stopPropagation();
    }
  };

  static defaultProps: DefaultProps = {
    disabled: false,
  };

  state: State = {
    isNewQuery: true,
    isEditingQuery: false,

    queryName: '',
  };

  onChangeInput = (event: React.FormEvent<HTMLInputElement>) => {
    const target = event.target as HTMLInputElement;
    this.setState({queryName: target.value});
  };

  /**
   * There are two ways to create a query
   * 1) Creating a query from scratch and saving it
   * 2) Modifying an existing query and saving it
   */
  handleCreateQuery = (event: React.MouseEvent<Element>) => {
    event.preventDefault();
    event.stopPropagation();

    const {api, organization, eventView, yAxis} = this.props;

    if (!this.state.queryName) {
      return;
    }

    const nextEventView = eventView.clone();
    nextEventView.name = this.state.queryName;

    // Checks if "Save as" button is clicked from a clean state, or it is
    // clicked while modifying an existing query
    const isNewQuery = !eventView.id;

    handleCreateQuery(api, organization, nextEventView, yAxis, isNewQuery).then(
      (savedQuery: SavedQuery) => {
        const view = EventView.fromSavedQuery(savedQuery);

        Banner.dismiss('discover');
        this.setState({queryName: ''});
        browserHistory.push(view.getResultsViewUrlTarget(organization.slug));
      }
    );
  };

  handleUpdateQuery = (event: React.MouseEvent<Element>) => {
    event.preventDefault();
    event.stopPropagation();

    const {api, organization, eventView, updateCallback, yAxis, setSavedQuery} =
      this.props;

    handleUpdateQuery(api, organization, eventView, yAxis).then(
      (savedQuery: SavedQuery) => {
        const view = EventView.fromSavedQuery(savedQuery);
        setSavedQuery(savedQuery);
        this.setState({queryName: ''});
        browserHistory.push(view.getResultsViewShortUrlTarget(organization.slug));
        updateCallback();
      }
    );
  };

  handleDeleteQuery = (event: React.MouseEvent<Element>) => {
    event.preventDefault();
    event.stopPropagation();

    const {api, organization, eventView} = this.props;

    handleDeleteQuery(api, organization, eventView).then(() => {
      browserHistory.push({
        pathname: getDiscoverQueriesUrl(organization),
        query: {},
      });
    });
  };

  handleCreateAlertSuccess = () => {
    const {organization} = this.props;
    trackAnalyticsEvent({
      eventKey: 'discover_v2.create_alert_clicked',
      eventName: 'Discoverv2: Create alert clicked',
      status: 'success',
      organization_id: organization.id,
      url: window.location.href,
    });
  };

  renderButtonSaveAs(disabled: boolean) {
    const {queryName} = this.state;
    return (
      <SaveAsDropdown
        queryName={queryName}
        onChangeInput={this.onChangeInput}
        modifiedHandleCreateQuery={this.handleCreateQuery}
        disabled={disabled}
      />
    );
  }

  renderButtonSave(disabled: boolean) {
    const {isNewQuery, isEditingQuery} = this.state;

    // Existing query that hasn't been modified.
    if (!isNewQuery && !isEditingQuery) {
      return (
        <Button
          icon={<IconStar color="yellow100" isSolid size="sm" />}
          disabled
          data-test-id="discover2-savedquery-button-saved"
        >
          {t('Saved for Org')}
        </Button>
      );
    }
    // Existing query with edits, show save and save as.
    if (!isNewQuery && isEditingQuery) {
      return (
        <Fragment>
          <Button
            onClick={this.handleUpdateQuery}
            data-test-id="discover2-savedquery-button-update"
            disabled={disabled}
          >
            <IconUpdate />
            {t('Save Changes')}
          </Button>
          {this.renderButtonSaveAs(disabled)}
        </Fragment>
      );
    }

    // Is a new query enable saveas
    return this.renderButtonSaveAs(disabled);
  }

  renderButtonDelete(disabled: boolean) {
    const {isNewQuery} = this.state;

    if (isNewQuery) {
      return null;
    }

    return (
      <Button
        data-test-id="discover2-savedquery-button-delete"
        onClick={this.handleDeleteQuery}
        disabled={disabled}
        icon={<IconDelete />}
        aria-label={t('Delete')}
      />
    );
  }

  renderButtonCreateAlert() {
    const {eventView, organization, projects} = this.props;

    return (
      <GuideAnchor target="create_alert_from_discover">
        <CreateAlertFromViewButton
          eventView={eventView}
          organization={organization}
          projects={projects}
          onClick={this.handleCreateAlertSuccess}
          referrer="discover"
          aria-label={t('Create Alert')}
          data-test-id="discover2-create-from-discover"
        />
      </GuideAnchor>
    );
  }

  renderButtonAddToDashboard() {
    const {organization, eventView, savedQuery, yAxis, router, location} = this.props;
    return (
      <Button
        key="add-dashboard-widget-from-discover"
        data-test-id="add-dashboard-widget-from-discover"
        onClick={() =>
          handleAddQueryToDashboard({
            organization,
            location,
            eventView,
            query: savedQuery,
            yAxis,
            router,
          })
        }
      >
        {t('Add to Dashboard')}
      </Button>
    );
  }

  renderSaveAsHomepage() {
    const {api, organization, eventView} = this.props;
    return (
      <Button
        key="save-query-as-homepage"
        data-test-id="save-query-as-homepage"
        onClick={() => {
          handleUpdateHomepageQuery(api, organization, eventView.toNewQuery());
        }}
      >
        {t('Use as Discover Home')}
      </Button>
    );
  }

  render() {
    const {organization} = this.props;

    const renderDisabled = p => (
      <Hovercard
        body={
          <FeatureDisabled
            features={p.features}
            hideHelpToggle
            message={t('Discover queries are disabled')}
            featureName={t('Discover queries')}
          />
        }
      >
        {p.children(p)}
      </Hovercard>
    );

    const renderQueryButton = (renderFunc: (disabled: boolean) => React.ReactNode) => {
      return (
        <Feature
          organization={organization}
          features={['discover-query']}
          hookName="feature-disabled:discover-saved-query-create"
          renderDisabled={renderDisabled}
        >
          {({hasFeature}) => renderFunc(!hasFeature || this.props.disabled)}
        </Feature>
      );
    };

    return (
      <ResponsiveButtonBar gap={1}>
        <Feature
          organization={organization}
          features={['discover-query', 'discover-query-builder-as-landing-page']}
        >
          {({hasFeature}) => hasFeature && this.renderSaveAsHomepage()}
        </Feature>
        {renderQueryButton(disabled => this.renderButtonSave(disabled))}
        <Feature organization={organization} features={['incidents']}>
          {({hasFeature}) => hasFeature && this.renderButtonCreateAlert()}
        </Feature>
        <Feature organization={organization} features={['dashboards-edit']}>
          {({hasFeature}) => hasFeature && this.renderButtonAddToDashboard()}
        </Feature>
        {renderQueryButton(disabled => this.renderButtonDelete(disabled))}
      </ResponsiveButtonBar>
    );
  }
}

const ResponsiveButtonBar = styled(ButtonBar)`
  @media (min-width: ${p => p.theme.breakpoints.medium}) {
    margin-top: 0;
  }
`;

const StyledOverlay = styled(Overlay)`
  padding: ${space(1)};
`;

const SaveAsButton = styled(Button)`
  width: 100%;
`;

const SaveAsInput = styled(InputControl)`
  height: 40px;
  margin-bottom: ${space(1)};
`;

const IconUpdate = styled('div')`
  display: inline-block;
  width: 10px;
  height: 10px;

  margin-right: ${space(0.75)};
  border-radius: 5px;
  background-color: ${p => p.theme.yellow300};
`;

export default withProjects(withApi(SavedQueryButtonGroup));
