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

from crispy_forms.helper import FormHelper
from deposit.forms import FormWithAbstract
from deposit.hal.metadata import HAL_TOPIC_CHOICES
from django import forms
from django.utils.translation import ugettext as __

from autocomplete.widgets import Select2

HAL_TOPIC_CHOICES = [
    ('CHIM', __('Chemistry')),
    ('INFO', __('Computer science')),
    ('MATH', __('Mathematics')),
    ('PHYS', __('Physics')),
    ('NLIN', __('Non-linear science')),
    ('SCCO', __('Cognitive science')),
    ('SDE', __('Environment sciences')),
    ('SDU', __('Planet and Universe')),
    ('SHS', __('Humanities and Social Science')),
    ('SDV', __('Life sciences')),
    ('SPI', __('Engineering sciences')),
    ('STAT', __('Statistics')),
    ('QFIN', __('Economy and quantitative finance')),
    ('OTHER', __('Other')),
  ]


class HALForm(FormWithAbstract):

#    def __init__(self, *args, **kwargs):
#        super(HALForm, self).__init__(*args, **kwargs)
#        self.helper = FormHelper(self)
#        self.helper.form_class = 'form-horizontal'
#        self.helper.label_class = 'col-lg-2'
#        self.helper.field_class = 'col-lg-8'

    # Dummy field to store the user name
    # (required for affiliation autocompletion)
    first_name = forms.CharField(
        required=False,
        widget=forms.HiddenInput
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.HiddenInput
    )

    topic = forms.ChoiceField(
            label=__('Scientific field'),
            choices=HAL_TOPIC_CHOICES)

    affiliation = forms.CharField(
        required=False,
        label=__('Affiliation'),
        widget=Select2(forward=['first_name', 'last_name'], url='autocomplete_affiliations')
    )
