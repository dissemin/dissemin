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
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __

from deposit.models import *
from upload.models import UploadedPDF
from papers.models import UPLOAD_TYPE_CHOICES

class PaperDepositForm(forms.Form):
    file_id = forms.IntegerField()
    radioUploadType = forms.ChoiceField(label=_('Upload type'), choices = UPLOAD_TYPE_CHOICES)

    def clean_file_id(self):
        id = self.cleaned_data['file_id']
        try:
            uploadedPDF = UploadedPDF.objects.get(pk=id)
        except UploadedPDF.NotFound:
            raise forms.ValidationError(__("Invalid full text identifier."), code='invalid_file_id')
        return uploadedPDF

