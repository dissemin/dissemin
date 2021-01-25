from urllib.parse import urlencode
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView
from django.views.generic.base import TemplateView

from shibboleth_discovery.mixins import ShibDSLoginMixin

from deposit.models import DepositRecord
from deposit.models import Repository
from website.forms import StartPageSearchForm
from statistics.models import COMBINED_STATUS_CHOICES

class StartPageView(TemplateView):

    template_name = 'dissemin/start_page.html'

    def get_context_data(self, **kwargs):
        """
        Here we add the search form, open access status information and the last latest deposits
        """
        context = super().get_context_data(**kwargs)
        context['search_form'] = StartPageSearchForm()
        context['combined_status'] = [{
            'choice_value' : v,
            'choice_label' : l,
            }
            for v, l in COMBINED_STATUS_CHOICES
        ]
        # Fetches last 5 DepositRecords that are published, newest first.
        context['latest_deposits'] = DepositRecord.objects.filter(
            status='published'
        ).select_related(
            'oairecord',
            'paper',
            'repository'
        ).order_by(
            '-pub_date'
        )[:5]

        return context

class LoginView(ShibDSLoginMixin, TemplateView):
    """
    This is a login view using shibboleth mixin
    """

    template_name = 'dissemin/login.html'


class LogoutView(RedirectView):

    url = reverse_lazy('start-page')

    def get_redirect_url(self, *args, **kwargs):
        """
        We logout the user. If a shibboleth logout url is given, we redirect to this url with a return self.url, otherwise we redirect directly
        """
        logout(self.request)
        if hasattr(settings, 'SHIBBOLETH_LOGOUT_URL'):
            target = urljoin('https://{}'.format(get_current_site(self.request)), str(self.url))
            params = {
                'return' : target,
            }
            self.url = '{}?{}'.format(
                settings.SHIBBOLETH_LOGOUT_URL,
                urlencode(params)
            )
        return self.url


class TOSView(TemplateView):
    
    template_name='dissemin/tos.html'

    def get_context_data(self, **kwargs):
        """
        We add the repositories
        """
        context = super().get_context_data(**kwargs)

        context['active_repositories'] = Repository.objects.filter(enabled=True)

        return context

