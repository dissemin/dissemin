#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#


import re
from deposit.forms import FormWithAbstract
from django import forms
from django.forms.utils import ValidationError
from deposit.osf.models import OSFDepositPreferences
from django.utils.translation import ugettext as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

# LICENSES ID FOR TEST-API.OSF.IO
OSF_SANDBOX_LICENSES_CHOICES = [
    ('58fd62fcda3e2400012ca5d3',
        _('Creative Commons CC0 1.0 Universal')),
    ('58fd62fcda3e2400012ca5d1',
        _('Creative Commons CC-By ' +
            'Attribution 4.0 International (CC BY 4.0)')),
    ('58fd62fcda3e2400012ca5cc',
        _('No license')),
]

# ORIGINAL LICENCES ID
OSF_LICENSES_CHOICES = [
    ('563c1cf88c5e4a3877f9e96c',
        _('Creative Commons CC0 1.0 Universal')),
    ('563c1cf88c5e4a3877f9e96a',
        _('Creative Commons CC-By ' +
            'Attribution 4.0 International (CC BY 4.0)')),
    ('563c1cf88c5e4a3877f9e965',
        _('No license')),
]

# SUBJECTS ID FOR TEST-API.OSF.IO
OSF_SANDBOX_SUBJECTS_CHOICES = [
    ('59552883da3e240081ba32ab',
        _('Architecture')),
    ('59552881da3e240081ba3203',
        _('Arts and Humanities')),
    ('59552881da3e240081ba3207',
        _('Business')),
    ('59552883da3e240081ba3289',
        _('Education')),
    ('59552884da3e240081ba32de',
        _('Engineering')),
    ('59552881da3e240081ba31ee',
        _('Law')),
    ('59552881da3e240081ba3210',
        _('Life Sciences')),
    ('59552881da3e240081ba3231',
        _('Medicine and Health Sciences')),
    ('59552883da3e240081ba32aa',
        _('Physical Sciences and Mathematics')),
    ('59552882da3e240081ba327a',
        _('Social and Behavioral Sciences')),
]

OSF_SUBJECTS_CHOICES = [
    ('584240d954be81056ceca9e5',
        _('Architecture')),
    ('584240da54be81056cecaab4',
        _('Arts and Humanities')),
    ('584240d954be81056ceca84d',
        _('Business')),
    ('584240da54be81056cecaae5',
        _('Education')),
    ('584240da54be81056cecaca9',
        _('Engineering')),
    ('584240db54be81056cecacd3',
        _('Law')),
    ('584240da54be81056cecaab0',
        _('Life Sciences')),
    ('584240da54be81056cecaaaa',
        _('Medicine and Health Sciences')),
    ('584240d954be81056ceca9a1',
        _('Physical Sciences and Mathematics')),
    ('584240da54be81056cecac48',
        _('Social and Behavioral Sciences')),
]


class OSFForm(FormWithAbstract):
    license = forms.ChoiceField(
        label=_('License'),
        choices=OSF_SANDBOX_LICENSES_CHOICES,
        initial='563c1cf88c5e4a3877f9e965',
        widget=forms.RadioSelect(attrs={'class': 'radio-margin'}))

    abstract = forms.CharField(
        min_length=20,
        widget=forms.Textarea)

    tags = forms.CharField(help_text="Separate tags with commas")

    subjects = forms.MultipleChoiceField(
        required=True,
        widget=forms.CheckboxSelectMultiple(),
        error_messages={'required': 'At least one subject is required.'},
        choices=OSF_SANDBOX_SUBJECTS_CHOICES
    )

    def __init__(self, paper, endpoint, **kwargs):
        super(OSFForm, self).__init__(endpoint, **kwargs)

        self.endpoint = endpoint

        if self.endpoint == "https://api.osf.io/":
            self.fields['license'].choices = OSF_LICENSES_CHOICES
            self.fields['subjects'].choices = OSF_SUBJECTS_CHOICES

class OSFPreferencesForm(forms.ModelForm):
    class Meta:
        model = OSFDepositPreferences
        fields = ['on_behalf_of']

    def __init__(self, *args, **kwargs):
        super(OSFPreferencesForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.add_input(
            Submit('submit', _('Save')),
        )

    def clean_on_behalf_of(self):
        r = re.compile('^[0-9a-z]+$')
        username = self.cleaned_data['on_behalf_of']
        if not r.match(username):
            raise ValidationError(_('Invalid OSF identifier.'), code='invalid-osf-id')
        return username


