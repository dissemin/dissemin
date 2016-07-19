# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(is_safe=True)
def doi_to_url(doi):
    return mark_safe('http://dx.doi.org/'+escape(doi.doi))
