# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

register = template.Library()

@register.filter(is_safe=True)
def authorlink(author):
    if author.researcher:
        return mark_safe('<a href="'+reverse('researcher', kwargs={'pk':author.researcher.id})+'">'+escape(unicode(author))+'</a>')
    else:
        return mark_safe(escape(unicode(author)))
