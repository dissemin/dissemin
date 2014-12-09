# -*- encoding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext as _

from papers.models import *

class AddResearcherForm(forms.Form):
    first = forms.CharField(label=_('First name'), max_length=256, min_length=2)
    last = forms.CharField(label=_('Last name'), max_length=256, min_length=2)
    department = forms.ModelChoiceField(label=_('Department'), queryset=Department.objects.all())
    email = forms.EmailField(label=_('Email'), required=False)
    homepage = forms.URLField(label=_('Homepage'),required=False)
    role = forms.URLField(label=_('Role'),required=False)


