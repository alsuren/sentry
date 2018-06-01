from __future__ import absolute_import, print_function

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache

from sentry.models import Identity, IdentityProvider, IdentityStatus
from sentry.identity.pipeline import IdentityProviderPipeline
from sentry.web.frontend.base import OrganizationView, BaseView
from sentry.web.helpers import render_to_response

IDENTITY_LINKED = _("Your {identity_provider} account has been associated with your Sentry account")


class AccountIdentityAssociateView(OrganizationView):
    @never_cache
    def handle(self, request, organization, provider_key, external_id):
        try:
            provider_model = IdentityProvider.objects.get(
                type=provider_key,
                external_id=external_id,
            )
        except IdentityProvider.DoesNotExist:
            return self.redirect(reverse('sentry-account-settings-identities'))

        pipeline = IdentityProviderPipeline(
            organization=organization,
            provider_key=provider_key,
            provider_model=provider_model,
            request=request,
        )

        if request.method != 'POST' and not pipeline.is_valid():
            context = {
                'provider': pipeline.provider,
                'organization': organization,
            }
            return render_to_response('sentry/auth-link-identity.html', context, request)

        pipeline.initialize()

        result = pipeline.current_step()

        # If the pipeline finished successfully it should return a dict with identity info.
        if not isinstance(result, dict):
            return result

        defaults = {
            'status': IdentityStatus.VALID,
            'scopes': result.get('scopes', []),
            'data': result.get('data', {}),
            'date_verified': timezone.now(),
        }

        identity, created = Identity.objects.get_or_create(
            idp=provider_model,
            user=request.user,
            external_id=result['id'],
            defaults=defaults,
        )

        if not created:
            identity.update(**defaults)

        messages.add_message(self.request, messages.SUCCESS, IDENTITY_LINKED.format(
            identity_provider=pipeline.provider.name,
        ))

        # TODO(epurkhiser): When we have more identities and have built out an
        # identity management page that supports these new identities (not
        # social-auth ones), redirect to the identities page.
        return HttpResponseRedirect(reverse('sentry-account-settings'))


class AccountIdentityLinkView(BaseView):
    @never_cache
    def handle(self, request):
        pipeline = IdentityProviderPipeline.get_for_request(request)

        if pipeline is None or not pipeline.is_valid():
            return self.redirect(reverse('sentry-account-settings-identities'))

        return pipeline.current_step()
