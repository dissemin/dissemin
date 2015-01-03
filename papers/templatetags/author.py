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
        return mark_safe('<a href="'+reverse('researcher', kwargs={'researcher':author.researcher.id})+'">'+escape(unicode(author.name))+'</a>')
    else:
        return mark_safe(escape(unicode(author.name)))

@register.filter(is_safe=True)
def publication(publi):
    if publi.journal:
        result = '<a href="'+reverse('journal', kwargs={'journal':publi.journal.id})+'"><emph>'+escape(unicode(publi.journal.title))+'</emph></a>'
    else:
        result = escape(unicode(publi.title))
    if publi.issue or publi.volume or publi.pages or publi.pubdate:
        result += ', '
    if publi.issue:
        result += '<strong>'+escape(unicode(publi.issue))+'</strong>'
    if publi.volume:
        result += '('+escape(unicode(publi.volume))+')'
    if (publi.issue or publi.volume) and publi.pubdate:
        result += ', '
    if publi.pubdate:
        result += escape(unicode(str(publi.pubdate.year)))
    return mark_safe(result)
