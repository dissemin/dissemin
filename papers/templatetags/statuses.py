# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from papers.models import OA_STATUS_CHOICES, PDF_STATUS_CHOICES
from django.utils.translation import ugettext as _

register = template.Library()

@register.filter(is_safe=True)
def explain_oa_status(status):
    for s in OA_STATUS_CHOICES:
        if status == s[0]:
            return mark_safe(s[1])
    return mark_safe(_('Unknown OA status'))

@register.filter(is_safe=True)
def explain_pdf_status(status):
    for s in PDF_STATUS_CHOICES:
        if status == s[0]:
            return mark_safe(s[1])
    return mark_safe(_('Unknown PDF status'))



