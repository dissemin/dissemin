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

from dissemin.settings import DEPOSIT_CONTENT_TYPES, DEPOSIT_MAX_FILE_SIZE

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

class AddResearcherForm(forms.Form):
    first = forms.CharField(label=_('First name'), max_length=256, min_length=2)
    last = forms.CharField(label=_('Last name'), max_length=256, min_length=2)
    email = forms.EmailField(label=_('Email'), required=False)
    homepage = forms.URLField(label=_('Homepage'),required=False)
    role = forms.CharField(label=_('Role'),required=False)
    department = forms.ModelChoiceField(label=_('Department'), queryset=Department.objects.all())

class AddUnaffiliatedResearcherForm(forms.Form):
    first = forms.CharField(label=_('First name'), max_length=256, min_length=2, required=False)
    last = forms.CharField(label=_('Last name'), max_length=256, min_length=2, required=False)
    orcid = OrcidField(required=False)
    force = forms.CharField(max_length=32, required=False)

    def clean_first(self):
        first = self.cleaned_data.get('first')
        if first and has_only_initials(first):
            raise forms.ValidationError(_('Please spell out at least one name.'), code='initials')
        return first

    def clean(self):
        cleaned_data = super(AddUnaffiliatedResearcherForm, self).clean()
        print dict(self.errors)
        if not cleaned_data.get('orcid'):
            if cleaned_data.get('first') and not cleaned_data.get('last'):
                self.add_error('last',
                    forms.ValidationError(_('A last name is required.'), code='required'))
            elif not cleaned_data.get('first') and not cleaned_data.get('last') and 'orcid' not in self.errors:
                raise forms.ValidationError(_('A name or an ORCID identifier are required.'), code='empty')
        return cleaned_data


