# -*- encoding: utf-8 -*-


from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(is_safe=True)
def doi_to_url(doi):
    return mark_safe('https://doi.org/'+escape(doi.doi))
