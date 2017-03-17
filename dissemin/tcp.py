# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

def orcid_base_domain(request):
    from django.conf import settings
    return {'ORCID_BASE_DOMAIN':settings.ORCID_BASE_DOMAIN}
