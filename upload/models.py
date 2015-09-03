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
from django.contrib.auth.models import User

MAX_ORIG_NAME_LENGTH = 1024
THUMBNAIL_MAX_HEIGHT = 297/2
THUMBNAIL_MAX_WIDTH = 210/2

class UploadedPDF(models.Model):
    """
    A PDF file, plus some useful info about who/when/how it was uploaded.
    """

    #: The user who uploaded that file
    user = models.ForeignKey(User)
    #: When it was uploaded
    timestamp = models.DateTimeField(auto_now=True)
    #: How it was uploaded: either filename or URL
    orig_name = models.CharField(max_length=MAX_ORIG_NAME_LENGTH)
    #: Number of pages
    num_pages = models.IntegerField(default=0)

    #: The file itself
    file = models.FileField(upload_to='uploads/%Y/%m/%d')
    #: A thumbnail of the first page
    thumbnail = models.FileField(upload_to='thumbnails/')

    class Meta:
        verbose_name = 'Uploaded PDF'


