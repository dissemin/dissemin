# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()


@register.filter()
def get_pie_data(stats):
    return mark_safe(json.dumps(stats.pie_data()))
