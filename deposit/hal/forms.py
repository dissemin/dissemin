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
from crispy_forms.layout import Layout
from django import forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as __

from deposit.forms import BaseMetadataForm
from deposit.hal.metadataFormatter import HAL_TOPIC_CHOICES
from deposit.zenodo.protocol import ZENODO_LICENSES_CHOICES


class HALForm(BaseMetadataForm):

    def __init__(self, *args, **kwargs):
        super(HALForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'

    topic = forms.ChoiceField(
            label=__('Scientific field'),
            choices=HAL_TOPIC_CHOICES)
