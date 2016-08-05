# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from papers.models import OA_STATUS_CHOICES
from papers.models import PDF_STATUS_CHOICES

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


@register.filter(is_safe=True)
def explain_policy(status, arg):
    explanations = {
        ("can", "preprint"): _('Preprints can be archived.'),
        ("cannot", "preprint"): _('Preprints cannot be archived.'),
        ("restricted", "preprint"): _('Under the restrictions below, preprints can be archived.'),
        ("unclear", "preprint"): _('Preprints archiving policy unclear'),
        ("unknown", "preprint"): _('Preprints archiving policy unknown'),
        ("can", "postprint"): _('Postprints can be archived.'),
        ("cannot", "postprint"): _('Postprints cannot be archived.'),
        ("restricted", "postprint"): _('Under the restrictions below, postprints can be archived.'),
        ("unclear", "postprint"): _('Postprint archiving policy unclear.'),
        ("unknown", "postprint"): _('Postprint archiving policy unknown.'),
        ("can", "pdfversion"): _('Final versions can be archived.'),
        ("cannot", "pdfversion"): _('Final versions cannot be archived.'),
        ("restricted", "pdfversion"): _('Under the restrictions below, final versions can be archived.'),
        ("unclear", "pdfversion"): _('Final version archiving policy unclear.'),
        ("unknown", "pdfversion"): _('Final version archiving policy unknown.'),
        }
    return mark_safe(explanations.get((status, arg), _("Unknown policy")))


@register.filter(is_safe=True)
def explain_policy_short(status):
    explanations = {
        ("can"): _('archiving allowed.'),
        ("cannot"): _('archiving forbidden.'),
        ("restricted"): _('archiving restricted:'),
        ("unclear"): _('policy unclear.'),
        ("unknown"): _('policy unknown.'),
        }
    return mark_safe(explanations.get((status), _("policy unknown.")))


@register.filter(is_safe=True)
def explain_policy_short_no_punc(status):
    explanations = {
        ("can"): _('archiving allowed'),
        ("cannot"): _('archiving forbidden'),
        ("restricted"): _('archiving restricted'),
        ("unclear"): _('policy unclear'),
        ("unknown"): _('policy unknown'),
        }
    return mark_safe(explanations.get((status), _("policy unknown.")))


@register.filter(is_safe=True)
def helptext_oa_status(status):
    OA_STATUS_ = dict([(s[0], s[2]) for s in OA_STATUS_CHOICES])
    return OA_STATUS_.get(status, _('Unknown OA status'))


@register.filter(is_safe=True)
def logo_oa_status(status):
    OA_STATUS_IMG = {
        'OA': 'oa',
        'OK': 'couldbe',
        'NOK': 'closed',
        'UNK': 'unk',
    }
    return 'img/logos/' + OA_STATUS_IMG[status] + '.png'
