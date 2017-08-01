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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from __future__ import unicode_literals

from deposit.forms import FormWithAbstract
from django import forms
from django.utils.translation import ugettext as __

# LICENSES ID FOR TEST-API.OSF.IO
OSF_SANDBOX_LICENSES_CHOICES = [
    ('58fd62fcda3e2400012ca5d3',
        __('Creative Commons CC0 1.0 Universal')),
    ('58fd62fcda3e2400012ca5d1',
        __('Creative Commons CC-By Attribution 4.0 International (CC BY 4.0)')),
    ('58fd62fcda3e2400012ca5cc',
        __('No license')),
]

#ORIGINAL LICENCES ID
OSF_LICENSES_CHOICES = [
    ('563c1cf88c5e4a3877f9e96c',
        __('Creative Commons CC0 1.0 Universal')),
    ('563c1cf88c5e4a3877f9e96a',
        __('Creative Commons CC-By Attribution 4.0 International (CC BY 4.0)')),
    ('563c1cf88c5e4a3877f9e965',
        __('No license')),
]

# SUBJECTS ID FOR TEST-API.OSF.IO
OSF_SANDBOX_SUBJECTS_CHOICES = [
    ('59552883da3e240081ba32ab',
        __('Architecture')),
    ('59552881da3e240081ba3203',
        __('Arts and Humanities')),
    ('59552881da3e240081ba3207',
        __('Business')),
    ('59552883da3e240081ba3289',
        __('Education')),
    ('59552884da3e240081ba32de',
        __('Engineering')),
    ('59552881da3e240081ba31ee',
        __('Law')),
    ('59552881da3e240081ba3210',
        __('Life Sciences')),
    ('59552881da3e240081ba3231',
        __('Medicine and Health Sciences')),
    ('59552883da3e240081ba32aa',
        __('Physical Sciences and Mathematics')),
    ('59552882da3e240081ba327a',
        __('Social and Behavioral Sciences')),
]

OSF_SUBJECTS_CHOICES = [
    ('584240d954be81056ceca9e5',
        __('Architecture')),
    ('584240da54be81056cecaab4',
        __('Arts and Humanities')),
    ('584240d954be81056ceca84d',
        __('Business')),
    ('584240da54be81056cecaae5',
        __('Education')),
    ('584240da54be81056cecaca9',
        __('Engineering')),
    ('584240db54be81056cecacd3',
        __('Law')),
    ('584240da54be81056cecaab0',
        __('Life Sciences')),
    ('584240da54be81056cecaaaa',
        __('Medicine and Health Sciences')),
    ('584240d954be81056ceca9a1',
        __('Physical Sciences and Mathematics')),
    ('584240da54be81056cecac48',
        __('Social and Behavioral Sciences')),
]

class OSFForm(FormWithAbstract):
    license = forms.ChoiceField(
        label=__('License'),
        choices=OSF_SANDBOX_LICENSES_CHOICES,
        initial='563c1cf88c5e4a3877f9e965',
        widget=forms.RadioSelect(attrs={'class': 'radio-margin'}))

    abstract = forms.CharField(
        min_length=20,
        widget=forms.Textarea)

    tags = forms.CharField(help_text="Separate tags with commas")

    subjects = forms.MultipleChoiceField(
        # required=True,
        widget=forms.CheckboxSelectMultiple(),
        # error_messages={'required': 'At least one subject is required.'},
        choices=OSF_SANDBOX_SUBJECTS_CHOICES
    )

    def __init__(self, paper, endpoint, **kwargs):
        super(OSFForm, self).__init__(endpoint, **kwargs)

        self.endpoint = endpoint

        if self.endpoint == "https://api.osf.io/":
            self.fields['license'].choices = OSF_LICENSES_CHOICES
            self.fields['subjects'].choises = OSF_SUBJECTS_CHOICES
