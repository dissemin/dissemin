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

from django.core.urlresolvers import reverse
from django import forms
from django.utils.translation import ugettext as __

from deposit.zenodo.protocol import ZENODO_LICENSES_CHOICES

def wrap_with_prefetch_status(baseWidget, callback, fieldname):
    """
    Add a status text above the widget to display the prefetching status
    of the data in the field.
    """
    orig_render = baseWidget.render
    def new_render(self, name, value, attrs=None):
        base_html = orig_render(self, name, value, attrs)
        if value:
            return base_html
        return ('<span class="prefetchingFieldStatus" data-callback="%s" data-fieldid="%s" data-fieldname="%s" data-objfieldname="%s"></span>' % (callback,attrs['id'],name,fieldname))+base_html
    baseWidget.render = new_render
    return baseWidget


class ZenodoForm(forms.Form):
    # Dummy field to store the paper id (required for dynamic fetching of the abstract)
    paper_id = forms.IntegerField(
            required=False,
            widget=forms.HiddenInput
            )
    abstract = forms.CharField(
            label=__('Abstract'),
            required=True,
            widget=wrap_with_prefetch_status(forms.Textarea,
                reverse('ajax-waitForConsolidatedField'), 'paper_id')(attrs={'class':'form-control'})
            )
    license = forms.ChoiceField(
            label=__('License'),
            choices=ZENODO_LICENSES_CHOICES,
            initial='cc-by',
            widget=forms.RadioSelect(attrs={'class':'radio-margin'})
            )

