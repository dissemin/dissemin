# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

register = template.Library()

domain_re = re.compile(r'\s*(https?|ftp)://(([a-zA-Z0-9-_]+\.)+[a-zA-Z]+)/')

@register.filter(is_safe=True)
def domain(url):
    match = domain_re.match(url)
    if match:
        return mark_safe(escape(match.group(2)))
    else:
        return mark_safe('')
