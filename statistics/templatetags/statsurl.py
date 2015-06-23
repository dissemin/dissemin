# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from django.core.urlresolvers import reverse

register = template.Library()

@register.filter(is_safe=True)
def statsurl(object_id, criteria):
    if object_id is None or len(object_id) == 0:
        return mark_safe("#")
    args = escape(object_id)
    if criteria == 'oa':
        args += '&status=OA'
    elif criteria == 'ok':
        args += '&pdf=OK'
    elif criteria == 'couldbe':
        args += '&status=OK&pdf=NOK'
    elif criteria == 'unk':
        args += '&status=UNK&pdf=NOK'
    elif criteria == 'closed':
        args += '&status=NOK&pdf=NOK'
    return mark_safe(reverse('search')+'?'+args)


