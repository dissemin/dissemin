# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from papers.name import shorten_first_name

register = template.Library()


@register.filter(is_safe=True)
def fullname(user):
    result = user.username
    if user.last_name:
        firstname = user.first_name or ''
        shortened = shorten_first_name(firstname)
        result = shortened+' '+user.last_name
    return mark_safe(escape(unicode(result)))
