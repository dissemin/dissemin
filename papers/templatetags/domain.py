# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from papers.utils import extract_domain

register = template.Library()

@register.filter(is_safe=True)
def domain(url):
    domain = extract_domain(url)
    if domain:
        return mark_safe(escape(domain))
    else:
        return mark_safe('')
