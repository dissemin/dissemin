from django.views.generic.base import TemplateView

from shibboleth_discovery.mixins import ShibDSLoginMixin

from deposit.models import DepositRecord
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
