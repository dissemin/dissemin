# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

register = template.Library()

@register.filter(is_safe=True)
def authorlink(author):
    if author.name.is_known:
        return mark_safe('<a href="'+reverse('researcher', kwargs={'pk':author.name.researcher.id})+'">'+escape(unicode(author.name))+'</a>')
    else:
        return mark_safe(escape(unicode(author.name)))

@register.filter(is_safe=True)
def publicationlink(publication):
    if publication.journal:
        result = '<a href="'+reverse('journal', kwargs={'pk':publication.journal.id})+'">'+escape(unicode(publication.journal.title))+'</a>'
        result += publication.details_to_str()
        return mark_safe(result)
    else:
        return mark_safe(escape(unicode(publication)))
