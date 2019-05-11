import json

import bleach
import requests

from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponse
from django.utils.translation import gettext as _


HAL_API_STRUCTURE = (
    'https://api.archives-ouvertes.fr/ref/structure/'
)


def affiliation_autocomplete(request):
    """
        Fetch the affiliations from HAL API
        - FIXME: handle pagination if there is.
        - FIXME: what happens when no results?
        - FIXME: handle error for requests
    """
    # Structure name
    term = request.GET.get('term')

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

    # Fetch affiliations
    response = {
        'err': 'nil',
        'results': [],
    }
    if not term:
        return HttpResponse(json.dumps(response),
                            content_type='application/json')

    r = requests.get(HAL_API_STRUCTURE, params={
        'q': term,
        'wt': 'json',
        'rows': 20,
        'fl': 'docid,label_s,label_html,valid_s',
    })
    try:
        r.raise_for_status()
        affiliations = r.json()['response']['docs']
    except (requests.exceptions.HTTPError, KeyError):
        return HttpResponse(json.dumps(response),
                            content_type='application/json')

    if not affiliations:
        return HttpResponse(json.dumps(response),
                            content_type='application/json')

    # Render response
    response['results'] = []
    VALIDITIES = [
        {
            'i18n': _("Current institutions"),
            'filter': lambda val: val == 'VALID'
        },
        {
            'i18n': _("Unverified institutions"),
            'filter': lambda val: val == 'INCOMING'
        },
        {
            'i18n': _("Obsolete institutions"),
            'filter': lambda val: val == 'OLD'
        },
        {
            'i18n': '',
            'filter': lambda val: val not in ['VALID', 'INCOMING', 'OLD']
        },
    ]
    for validity in VALIDITIES:
        response['results'].append({
            'text': validity['i18n'],
            'children': [{
                'id': item['docid'],
                'text': item['label_s'],
                'html': bleach.clean(
                    item['label_html'],
                    tags=['dl', 'dt', 'span'],
                    attributes={'span': ['class']},
                    strip=True,
                    strip_comments=True
                ),
            } for item in affiliations if validity['filter'](item['valid_s'])]
        })
    return HttpResponse(json.dumps(response), content_type='application/json')
