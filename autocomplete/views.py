from dal.views import ViewMixin
from dal_select2.views import Select2ViewMixin
from django.views.generic import View
from django.core.exceptions import SuspiciousOperation
import requests
import json


HAL_API_AUTHOR_STRUCTURE = (
    'https://api.archives-ouvertes.fr/search/authorstructure/'
)


class AffiliationAutocomplete(View, ViewMixin, Select2ViewMixin):
    """
        Fetch the affiliations from HAL API
        - FIXME: handle pagination if there is.
        - FIXME: what happens when no results?
        - FIXME: handle error for requests
    """
    # Never display option to create a new field.
    create_field = False

    def get_result_value(self, result):
        return result[1]

    def get_result_label(self, result):
        return result[0]

    def has_more(self, context):
        return context.get('has_more', False)

    def fetch_affiliations(self, author):
        r = requests.get(HAL_API_AUTHOR_STRUCTURE, params={
            'firstName_t': author['first_name'],
            'lastName_t': author['last_name'],
            'wt': 'json'
        })
        r.raise_for_status()
        affiliations = r.json()['response']['result']

        if not affiliations:
            return {
                'object_list': [],
                'has_more': False
            }

        affiliations = affiliations['org']

        return {
            'object_list': [(
                aff['orgName'][0],
                aff['idno']
            ) for aff in affiliations
                if 'idno' in aff],
            'has_more': False
        }

    def get(self, request, *args, **kwargs):
        context = {}

        # Author data
        first_name = request.GET.get('first_name', None)
        last_name = request.GET.get('last_name', None)

        try:
            forward = request.GET.get('forward', None)
            if forward is not None:
                forward = json.loads(forward)
        except:
            raise SuspiciousOperation('forward is not proper JSON object')

        if not first_name and not last_name and forward:
            first_name = forward.get('first_name', None)
            last_name = forward.get('last_name', None)

        if not first_name:
            raise SuspiciousOperation(
                'first_name is missing'
            )

        if not last_name:
            raise SuspiciousOperation(
                'last_name is missing'
            )

        context = self.fetch_affiliations({
            'first_name': first_name,
            'last_name': last_name
        })

        return self.render_to_response(context)
