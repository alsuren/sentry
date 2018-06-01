from __future__ import absolute_import, print_function

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from sentry.models import IdentityProvider
from sentry.pipeline import Pipeline

from . import default_manager

IDENTITY_LINKED = _("Your {identity_provider} account has been associated with your Sentry account")

logger = logging.getLogger('sentry.identity')


class IdentityProviderPipeline(Pipeline):
    logger = logger

    pipeline_name = 'identity_provider'
    provider_manager = default_manager
    provider_model_cls = IdentityProvider

    def redirect_url(self):
        associate_url = reverse('sentry-account-link-identity')

        # Use configured redirect_url if specified for the pipeline if available
        return self.config.get('redirect_url', associate_url)

    def finish_pipeline(self):
        """Returns a dictionary containing identity information obtained from the OAuth flow."""
        id_dict = self.provider.build_identity(self.state.data)
        self.state.clear()
        return id_dict
