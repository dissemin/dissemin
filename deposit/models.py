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
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django.db import models
from papers.models import Paper
from django.contrib.auth.models import User
from upload.models import UploadedPDF

DEPOSIT_STATUS_CHOICES = [
   ('created', _('Created')),
   ('metadata_defective', _('Metadata defective')),
   ('document_defective', _('Document defective')),
   ('deposited', _('Deposited')),
   ]

ZENODO_LICENSES_CHOICES = [
   ('cc-zero', _('CC 0')),
   ('cc-by', _('CC BY')),
   ('cc-by-sa', _('CC BY SA')),
 ]

class DepositRecord(models.Model):
    paper = models.ForeignKey(Paper)
    user = models.ForeignKey(User)

    request = models.TextField(null=True, blank=True)
    identifier = models.CharField(max_length=512, null=True, blank=True)
    #deposition id on zenodo/hal/whatever
    pdf_url = models.URLField(max_length=1024, null=True, blank=True)
    date = models.DateTimeField(auto_now=True) # deposit date
    upload_type = models.CharFile = models.FileField(upload_to='deposits')

    file = models.ForeignKey(UploadedPDF)

    class Meta:
        db_table = 'papers_depositrecord'

    def __unicode__(self):
        if self.identifier:
            return self.identifier
        else:
            return _('Deposit')


