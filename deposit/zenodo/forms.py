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
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as __

from deposit.forms import BaseMetadataForm

ZENODO_LICENSES_CHOICES = [
   ('cc-zero',
    __('Creative Commons CCZero (CC0)')),
   ('cc-by',
    __('Creative Commons Attribution (CC-BY)')),
   ('cc-by-sa',
    __('Creative Commons Attribution-ShareAlike (CC-BY-SA)')),
   ('cc-by-nc-4.0',
    __('Creative Commons Attribution-NonCommercial (CC-BY-NC)')),
   ('cc-by-nd-4.0',
    __('Creative Commons Attribution-NoDerivatives (CC-BY-ND)')),
   ('other-open',
    __('Other open license')),
 ]


class ZenodoForm(BaseMetadataForm):
    license = forms.ChoiceField(
            label=__('License'),
            choices=ZENODO_LICENSES_CHOICES,
            initial='other-open',
            widget=forms.RadioSelect(attrs={'class': 'radio-margin'})
            )
