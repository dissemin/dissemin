# -*- encoding: utf-8 -*-


from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.urls import reverse

register = template.Library()


@register.filter(is_safe=True)
def authorlink(author):
    url = reverse('search')+'?authors='+author.name.full.replace(' ','+')
    if author.researcher_id:
        url = author.researcher.url
    elif author.orcid:
        url = reverse('researcher-by-orcid', kwargs={'orcid':author.orcid})
    return mark_safe('<a href="'+url+'">'+escape(str(author.name))+'</a>')


@register.filter(is_safe=True)
def publication(publi):
    result = ''
    if publi.publisher_id:
        if publi.publisher.canonical_url:
            result += '<a href="'+publi.publisher.canonical_url + \
                '">'+escape(publi.publisher.name)+'</a>, '
        else:
            result += escape(publi.publisher.name)+', '
    if publi.pubtype == 'book-chapter' and publi.journal and publi.container and publi.container != str(publi.journal):
        result += escape(str(publi.container))+', '
    if publi.journal:
        result += '<emph>'+escape(str(publi.journal.title))+'</emph>'
    else:
        result = escape(str(publi.journal_title))
    if publi.issue or publi.volume or publi.pages or publi.pubdate:
        result += ', '
    if publi.issue:
        result += '<strong>'+escape(str(publi.issue))+'</strong>'
    if publi.volume:
        result += '('+escape(str(publi.volume))+')'
    if (publi.issue or publi.volume) and (publi.pubdate or publi.pages):
        result += ', '
    if publi.pages:
        result += 'p. '+publi.pages
        if publi.pubdate:
            result += ', '
    if publi.pubdate:
        result += escape(str(str(publi.pubdate.year)))
    return mark_safe(result)
