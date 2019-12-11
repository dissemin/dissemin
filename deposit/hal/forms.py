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



from autocomplete.widgets import Select2
from deposit.forms import BaseMetadataForm
from deposit.hal.metadata import HAL_TOPIC_CHOICES
from django import forms
from django.utils.translation import ugettext as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from deposit.hal.models import HALDepositPreferences


class HALForm(BaseMetadataForm):

    def __init__(self, paper, **kwargs):
        super(HALForm, self).__init__(**kwargs)
        self.fields['depositing_author'].choices = enumerate(
            map(str, paper.authors))

    topic = forms.ChoiceField(
            label=_('Scientific field'),
            choices=HAL_TOPIC_CHOICES)

    depositing_author = forms.TypedChoiceField(
        required=True,
        label=_('Depositing author'),
        choices=[], # choices are initialized from the paper later on
        coerce=int, # values are indexes of authors
    )

    affiliation = forms.CharField(
        required=True,
        label=_('Affiliation'),
        widget=Select2(
            data_view='autocomplete-hal-affiliations',
            attrs={
                'style': 'width: 100%',
            },
        )
    )

class HALPreferencesForm(forms.ModelForm):
    class Meta:
        model = HALDepositPreferences
        fields = ['on_behalf_of']

    def __init__(self, *args, **kwargs):
        super(HALPreferencesForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(
            Submit('submit', _('Save')),
        )

