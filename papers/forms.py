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

from dissemin.settings import DEPOSIT_CONTENT_TYPES, DEPOSIT_MAX_FILE_SIZE

from papers.models import *
from upload.models import UploadedPDF

class AddResearcherForm(forms.Form):
    first = forms.CharField(label=_('First name'), max_length=256, min_length=2)
    last = forms.CharField(label=_('Last name'), max_length=256, min_length=2)
    department = forms.ModelChoiceField(label=_('Department'), queryset=Department.objects.all())
    email = forms.EmailField(label=_('Email'), required=False)
    homepage = forms.URLField(label=_('Homepage'),required=False)
    role = forms.CharField(label=_('Role'),required=False)

class PaperDepositForm(forms.Form):
    file_id = forms.IntegerField()
    radioUploadType = forms.ChoiceField(label=_('Upload type'), choices = UPLOAD_TYPE_CHOICES)

    def clean_file_id(self):
        id = self.cleaned_data['file_id']
        try:
            uploadedPDF = UploadedPDF.objects.get(pk=id)
        except UploadedPDF.NotFound:
            raise forms.ValidationError(_("Invalid full text identifier."), code='invalid_file_id')
        return uploadedPDF

