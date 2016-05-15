# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.contrib.staticfiles.templatetags.staticfiles import static

from django.conf import settings

register = template.Library()

@register.filter(is_safe=True)
def orcid_to_url(orcid):
    return mark_safe('http://{}/{}'.format(settings.ORCID_BASE_DOMAIN, escape(orcid))

@register.filter(is_safe=True)
def small_orcid(orcid):
    """
    We expect here that the ORCID id has been validated before.
    This displays something like "iD ...-1234-2349"
    """
    return mark_safe('<a href="%s" alt="%s"><img src="%s" alt="ORCID" /> ...%s</a>' %
            (orcid_to_url(orcid),
             orcid,
             static('img/orcid-small.png'),
             orcid[9:]))

@register.filter(is_safe=True)
def full_orcid(orcid):
    """
    We expect here that the ORCID id has been validated before
    This displays something like "iD 0000-0002-1234-2349"
    """
    return mark_safe('<a href="%s" alt="%s"><img src="%s" alt="ORCID" /> %s</a>' %
            (orcid_to_url(orcid),
             orcid,
             static('img/orcid-small.png'),
             orcid))
