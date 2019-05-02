import json

import requests

from dal.views import ViewMixin
from dal_select2.views import Select2ViewMixin
from django.core.exceptions import SuspiciousOperation
from django.views.generic import View


HAL_API_STRUCTURE = (
    'https://api.archives-ouvertes.fr/ref/structure/'
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
        return result['docid']

    def get_result_selection(self, result):
        return result['label_s']

    def get_result_result(self, result):
        return result['label_html']

    def get_result_valid(self, result):
        return result['valid_s']

    def get_results(self, context):
        return [
            {
                'id': self.get_result_value(result),
                'selection': self.get_result_selection(result),
                'result': self.get_result_result(result),
                'valid': self.get_result_valid(result)
            }
            for result in context['object_list']
        ]

    def has_more(self, context):
        return context.get('has_more', False)

    def fetch_affiliations(self, q):
        empty_resp = {
            'object_list': [],
            'has_more': False,
        }
        if not q:
            return empty_resp
        r = requests.get(HAL_API_STRUCTURE, params={
            'q': q,
            'wt': 'json',
            'rows': 20,
            'fl': 'docid,label_s,label_html,valid_s',
        })
        try:
            r.raise_for_status()
            affiliations = r.json()['response']['docs']
        except (requests.exceptions.HTTPError, KeyError):
            return empty_resp

        if not affiliations:
            return empty_resp

        return {
            'object_list': [aff for aff in affiliations
                if 'docid' in aff],
            'has_more': False
        }

    def get(self, request, *args, **kwargs):
        context = {}

        # Structure name
        q = request.GET.get('q')

        # Author data
        #first_name = request.GET.get('first_name', None)
        #last_name = request.GET.get('last_name', None)

        try:
            forward = request.GET.get('forward', None)
            if forward is not None:
                forward = json.loads(forward)
        except:
            raise SuspiciousOperation('forward is not proper JSON object')

        #if not first_name and not last_name and forward:
        #    first_name = forward.get('first_name', None)
        #    last_name = forward.get('last_name', None)

        #if not first_name:
        #    raise SuspiciousOperation(
        #        'first_name is missing'
        #    )

        #if not last_name:
        #    raise SuspiciousOperation(
        #        'last_name is missing'
        #    )

        context = self.fetch_affiliations(q)
        #{
        #    'first_name': first_name,
        #    'last_name': last_name
        #}

        return self.render_to_response(context)
