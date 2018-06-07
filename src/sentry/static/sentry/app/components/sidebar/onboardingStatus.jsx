import PropTypes from 'prop-types';
import React from 'react';

import {t} from '../../locale';
import analytics from 'app/utils/analytics';
import SidebarPanel from './sidebarPanel';
import TodoList from '../onboardingWizard/todos';
import Tooltip from '../tooltip';

class OnboardingStatus extends React.Component {
  static propTypes = {
    org: PropTypes.object.isRequired,
    currentPanel: PropTypes.string,
    onShowPanel: PropTypes.func,
    showPanel: PropTypes.bool,
    hidePanel: PropTypes.func,
    collapsed: PropTypes.bool,
  };

  shouldComponentUpdate(nextProps, nextState) {
    if (this.props.currentPanel !== nextProps.currentPanel &&
      (this.props.currentPanel || nextProps.currentPanel == 'todos')) {
        this.recordAnalytics(this.props.currentPanel);
    };
    return true;
  };

  recordAnalytics(currentPanel){
    orgId = this.props.org.id;
    if (currentPanel == 'todos') {
      analytics('onboarding.wizard_closed', {org_id: orgId} );
    }else{
      analytics('onboarding.wizard_opened', {org_id: orgId} );
    }
  };

  render() {
    let {collapsed, org, currentPanel, hidePanel, showPanel, onShowPanel} = this.props;
    if (org.features && org.features.indexOf('onboarding') === -1) return null;

    let doneTasks = (org.onboardingTasks || []).filter(
      task => task.status === 'complete' || task.status === 'skipped'
    );
    let allDisplayedTasks = TodoList.TASKS.filter(task => task.display);

    let percentage = Math.round(
      doneTasks.length / allDisplayedTasks.length * 100
    ).toString();

    let style = {
      height: collapsed ? percentage + '%' : undefined,
      width: collapsed ? undefined : percentage + '%',
    };

    if (doneTasks.length >= allDisplayedTasks.length) {
      return null;
    }

    return (
      <div className={currentPanel === 'todos' ? 'onboarding active' : 'onboarding'}>
        <Tooltip
          title={t(
            `Getting started with Sentry: <br />${doneTasks.length} / ${allDisplayedTasks.length} tasks completed`
          )}
          tooltipOptions={{html: true}}
        >
          <div
            data-test-id="onboarding-progress-bar"
            className="onboarding-progress-bar"
            onClick={onShowPanel}
          >
            <div className="slider" style={style} />
          </div>
        </Tooltip>
        {showPanel &&
          currentPanel === 'todos' && (
            <SidebarPanel
              collapsed={collapsed}
              title="Getting Started with Sentry"
              hidePanel={hidePanel}
            >
              <TodoList />
            </SidebarPanel>
          )}
      </div>
    );
  }
}

export default OnboardingStatus;
