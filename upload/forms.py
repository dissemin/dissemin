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
from django.template.defaultfilters import filesizeformat
from dissemin.settings import DEPOSIT_CONTENT_TYPES, DEPOSIT_MAX_FILE_SIZE


invalid_content_type_message = _('Invalid file format: only PDF files are accepted.')

class AjaxUploadForm(forms.Form):
    upl = forms.FileField()

    def clean_upl(self):
        content = self.cleaned_data['upl']
        if content.content_type in DEPOSIT_CONTENT_TYPES:
            if content._size > DEPOSIT_MAX_FILE_SIZE:
                raise forms.ValidationError(_('File too large (%(size)s). Maximum size is %(maxsize)s.') %
                        {'size':filesizeformat(content._size),
                         'maxsize':filesizeformat(DEPOSIT_MAX_FILE_SIZE))},
                        code='too_large')
        else:
            raise forms.ValidationError(invalid_content_type_message, code='invalid_type')
        return content

class UrlDownloadForm(forms.Form):
    url = forms.URLField(label=_('URL'),required=True)

