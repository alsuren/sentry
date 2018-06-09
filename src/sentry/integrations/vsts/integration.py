from __future__ import absolute_import
from time import time

from django.utils.translation import ugettext_lazy as _
from sentry.integrations import Integration, IntegrationProvider, IntegrationMetadata
from .client import VstsApiClient
from sentry.pipeline import NestedPipelineView
from sentry.identity.pipeline import IdentityProviderPipeline
from sentry.identity.vsts import VSTSIdentityProvider
from sentry.utils.http import absolute_uri
DESCRIPTION = """
VSTS
"""

metadata = IntegrationMetadata(
    description=DESCRIPTION.strip(),
    author='The Sentry Team',
    noun=_('Account'),
    issue_url='https://github.com/getsentry/sentry/issues/new?title=VSTS%20Integration:%20&labels=Component%3A%20Integrations',
    source_url='https://github.com/getsentry/sentry/tree/master/src/sentry/integrations/vsts',
    aspects={},
)


class VstsIntegration(Integration):
    def __init__(self, *args, **kwargs):
        super(VstsIntegration, self).__init__(*args, **kwargs)
        self.default_identity = None

    def get_client(self):
        if self.default_identity is None:
            self.default_identity = self.get_default_identity()

        access_token = self.default_identity.data.get('access_token')
        if access_token is None:
            raise ValueError('Identity missing access token')
        return VstsApiClient(access_token)

    def get_project_config(self):
        client = self.get_client()
        projects = client.get_projects(self.model.metadata['domain_name'])
        project_choices = [(project['id'], project['name']) for project in projects['value']]
        default_project = self.org_integration.config.get('default_project')

        return [
            {
                'name': 'default_project',
                'type': 'choice',
                'allowEmpty': True,
                'required': True,
                'choices': project_choices,
                'initial': (default_project['id'], default_project['name']) if default_project is not None else ('', ''),
                # TODO(LB): Tried using ugettext_lazy but got <django.utils.functional.__proxy__ object at 0x107fb5110> is not JSON serializable
                # this was during the installation flow; decided to just move on instead
                # of worrying about it
                'label': 'Default Project Name',
                'placeholder': 'MyProject',
                'help': 'Enter the Visual Studio Team Services project name that you wish to use as a default for new work items',
            }
        ]


class VstsIntegrationProvider(IntegrationProvider):
    key = 'vsts'
    name = 'Visual Studio Team Services'
    metadata = metadata
    domain = '.visualstudio.com'
    api_version = '4.1'
    needs_default_identity = True
    integration_cls = VstsIntegration
    can_add_project = True

    setup_dialog_config = {
        'width': 600,
        'height': 800,
    }

    def get_pipeline_views(self):
        identity_pipeline_config = {
            'redirect_url': absolute_uri('/extensions/vsts/setup/'),
        }

        identity_pipeline_view = NestedPipelineView(
            bind_key='identity',
            provider_key='vsts',
            pipeline_cls=IdentityProviderPipeline,
            config=identity_pipeline_config,
        )

        return [
            identity_pipeline_view,
        ]

    def build_integration(self, state):
        data = state['identity']['data']
        account = state['identity']['account']
        instance = state['identity']['instance']

        scopes = sorted(VSTSIdentityProvider.oauth_scopes)
        return {
            'name': account['AccountName'],
            'external_id': account['AccountId'],
            'metadata': {
                'domain_name': instance,
                'scopes': scopes,
            },
            # TODO(LB): Change this to a Microsoft account as opposed to a VSTS workspace
            'user_identity': {
                'type': 'vsts',
                'external_id': account['AccountId'],
                'scopes': [],
                'data': self.get_oauth_data(data),
            },
        }

    def get_oauth_data(self, payload):
        data = {'access_token': payload['access_token']}

        if 'expires_in' in payload:
            data['expires'] = int(time()) + int(payload['expires_in'])
        if 'refresh_token' in payload:
            data['refresh_token'] = payload['refresh_token']
        if 'token_type' in payload:
            data['token_type'] = payload['token_type']

        return data
