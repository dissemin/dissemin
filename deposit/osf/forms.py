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

# OSF_DISCIPLINES_CHOICES = [
#     ('584240d954be81056ceca9e5',
#         __('Architecture')),
#     ('584240da54be81056cecaab4',
#         __('Arts and Humanities')),
#     ('business',
#         __('Business')),
#     ('education',
#         __('Education')),
#     ('law',
#         __('Law')),
#     ('life_sciences',
#         __('Life Sciences')),
#     ('medicine',
#         __('Medicine and Health Sciences')),
#     ('phy_sci_maths',
#         __('Physical Sciences and Mathematics')),
#     ('social',
#         __('Social and Behavioral Sciences')),
# ]

class OSFForm(FormWithAbstract):
    def __init__(self, paper, endpoint, **kwargs):
        super(OSFForm, self).__init__(endpoint, **kwargs)

        self.endpoint = endpoint

        if self.endpoint == "https://test-api.osf.io/":
            self.choices = OSF_SANDBOX_LICENSES_CHOICES
        else:
            self.choices = OSF_LICENSES_CHOICES

        license = forms.ChoiceField(
            label=__('License'),
            choices=self.choices,
            initial='563c1cf88c5e4a3877f9e965',
            widget=forms.RadioSelect(attrs={'class': 'radio-margin'}))

        abstract = forms.CharField(
            min_length=20,
            widget=forms.Textarea)

        tags = forms.CharField(help_text="Separate tags with commas")

        # discipline = forms.MultipleChoiceField(
        #     required=False,
        #     widget=forms.CheckboxSelectMultiple(),
        #     choices=OSF_DISCIPLINES_CHOICES,
        # )
