# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

from __future__ import unicode_literals
from django import forms
from django.utils.translation import ugettext as _

from papers.models import *
from papers.name import *
from upload.models import UploadedPDF

class OrcidField(forms.CharField):
    def to_python(self, val):
        if not val:
            return
        cleaned_val = validate_orcid(val)
        if cleaned_val is None:
            raise forms.ValidationError(_('Invalid ORCID identifier.'), code='invalid')
        return cleaned_val

class ResearcherDepartmentForm(forms.Form):
    value = forms.ModelChoiceField(label=_('Department'), queryset=Department.objects.all())
    pk = forms.ModelChoiceField(label=_('Researcher'), queryset=Researcher.objects.all(), widget=forms.HiddenInput())
    name = forms.CharField(widget=forms.HiddenInput(), initial='department_id')

class AddUnaffiliatedResearcherForm(forms.Form):
    first = forms.CharField(label=_('First name'), max_length=256, min_length=2, required=False)
    last = forms.CharField(label=_('Last name'), max_length=256, min_length=2, required=False)
    force = forms.CharField(max_length=32, required=False)

    def clean_first(self):
        first = self.cleaned_data.get('first')
        if first and has_only_initials(first):
            raise forms.ValidationError(_('Please spell out at least one name.'), code='initials')
        return first

    def clean(self):
        cleaned_data = super(AddUnaffiliatedResearcherForm, self).clean()
        if not cleaned_data.get('first') or not cleaned_data.get('last'):
            if not cleaned_data.get('last'):
                self.add_error('last',
                    forms.ValidationError(_('A last name is required.'), code='required'))
            else:
                self.add_error('first',
                    forms.ValidationError(_('A first name is required.'), code='required'))
        return cleaned_data


