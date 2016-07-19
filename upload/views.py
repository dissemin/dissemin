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

from datetime import datetime
import json
from StringIO import StringIO

from django.contrib.auth.decorators import user_passes_test
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from jsonview.decorators import json_view
import PyPDF2
from PyPDF2.utils import PyPdfError
import requests
from requests.packages.urllib3.exceptions import HTTPError
from requests.packages.urllib3.exceptions import ReadTimeoutError
import wand.exceptions
import wand.image

from dissemin.settings import DEPOSIT_MAX_FILE_SIZE
from dissemin.settings import URL_DEPOSIT_DOWNLOAD_TIMEOUT
from papers.user import *
from upload.forms import *
from upload.models import *


# AJAX upload


@json_view
@require_POST
@user_passes_test(is_authenticated)
def handleAjaxUpload(request):
    form = AjaxUploadForm(request.POST, request.FILES)
    if form.is_valid():
        # We read the whole file in memory, which
        # is reasonably safe because we know it's not too big
        pdf_file = request.FILES['upl'].read()
        orig_name = request.FILES['upl'].name

        status = save_pdf(request.user, orig_name, pdf_file)

        if status['status'] == 'error':
            status['upl'] = status['message']
            return status, 403

        return status
    else:
        return form.errors, 403


def make_thumbnail(pdf_blob):
    """
    Takes a PDF file (represented as a string) and returns a pair:
    - the number of pages
    - a thumbnail of its first page in PNG (as a string again),
    or None if anything failed.
    """
    try:
        resolution = int(THUMBNAIL_MAX_WIDTH / (21/2.54))+1
        num_pages = None

        first_blob = False
        try:  # We try to extract the first page of the PDF
            orig_pdf = StringIO(pdf_blob)
            reader = PyPDF2.PdfFileReader(orig_pdf)
            num_pages = reader.getNumPages()
            if not reader.isEncrypted and num_pages == 0:
                print "No pages"
                return
            writer = PyPDF2.PdfFileWriter()
            writer.addPage(reader.getPage(0))
            first_page = StringIO()
            writer.write(first_page)
            first_blob = first_page.getvalue()
        except PyPdfError as e:
            # PyPDF2 failed (maybe it believes the file is encrypted…)
            # We try to convert the file with ImageMagick (wand) anyway,
            # rendering the whole PDF as we have not been able to
            # select the first page
            print "PyPDF error: "+str(e)
            first_blob = pdf_blob

        # We render the PDF (or only its first page if we succeeded to extract
        # it)
        with wand.image.Image(blob=pdf_blob, format='pdf', resolution=resolution) as image:
            if image.height == 0 or image.width == 0:
                print "0 width or height"
                return
            if num_pages is None:
                num_pages = len(image.sequence)
            if num_pages == 0:
                print "No pages"
                return
            image = wand.image.Image(image=image.sequence[0])

            # Resizing disabled, we computed a reasonable resolution.
            # But anyway it costs much less than rendering…

            #ratio = float(image.width)/image.height
            #ref_ratio = float(THUMBNAIL_MAX_WIDTH)/THUMBNAIL_MAX_HEIGHT
            # if ratio < ref_ratio:
            #    new_height = THUMBNAIL_MAX_HEIGHT
            #    new_width = int(new_height * ratio)
            # else:
            #    new_width = THUMBNAIL_MAX_WIDTH
            #    new_height = int(new_width / ratio)
            # print "Resizing to %d/%d" % (new_height,new_width)
            #image.resize(new_width, new_height)

            image.format = 'png'
            return (num_pages, image.make_blob())
    except wand.exceptions.WandException as e:
        # Wand failed: we consider the PDF file as invalid
        print "Wand exception: "+unicode(e)
    except ValueError as e:
        print "ValueError: "+unicode(e)


def save_pdf(user, orig_name, pdf_blob):
    """
    Given a User and a PDF file represented as a stream,
    create the UploadedPDF object.

    :returns: the status context telling whether the operation has succeded.
    """

    response = {'status': 'error'}
    # Check that the file is a valid PDF by extracting the first page
    res = make_thumbnail(pdf_blob)
    if res is None:
        response['message'] = _('Invalid PDF file.')
        return response

    num_pages, png_blob = res

    # Otherwise we save the file!
    upload = UploadedPDF(
            user=user,
            num_pages=num_pages,
            orig_name=orig_name[:MAX_ORIG_NAME_LENGTH])
    f = ContentFile(pdf_blob)
    thumbnail_file = ContentFile(png_blob)
    upload.file.save('document.pdf', f)
    upload.thumbnail.save('thumbnail.png', thumbnail_file)
    upload.save()

    response = {
            'status': 'success',
            'size': len(pdf_blob),
            'num_pages': num_pages,
            'thumbnail': upload.thumbnail.url,
            'file_id': upload.id,
            }
    return response


@json_view
@require_POST
@user_passes_test(is_authenticated)
def handleUrlDownload(request):
    response = {'status': 'error'}
    form = UrlDownloadForm(request.POST)
    if not form.is_valid():
        response['message'] = _('Invalid form.')
        return response, 403
    content = None
    try:
        r = requests.get(form.cleaned_data[
                         'url'], timeout=URL_DEPOSIT_DOWNLOAD_TIMEOUT, stream=True)
        r.raise_for_status()
        content = r.raw.read(DEPOSIT_MAX_FILE_SIZE+1, decode_content=False)

        if len(content) > DEPOSIT_MAX_FILE_SIZE:
            response['message'] = _('File too large.')

        content_type = r.headers.get('content-type')
        if 'text/html' in content_type:
            response['message'] = (  # Left as one line for compatibility purposes
                _('Invalid content type: this link points to a web page, we need a direct link to a PDF file.'))

    except requests.exceptions.SSLError as e:
        response['message'] = _('Invalid SSL certificate on the remote server.')
    except requests.exceptions.Timeout as e:
        response['message'] = _('Invalid URL (server timed out).')
    except requests.exceptions.RequestException as e:
        response['message'] = _('Invalid URL.')
    except ReadTimeoutError as e:
        response['message'] = _('Invalid URL (server timed out).')
    except HTTPError as e:
        response['message'] = _('Invalid URL.')

    if 'message' in response:
        return response, 403

    orig_name = form.cleaned_data['url']

    response = save_pdf(request.user, orig_name, content)

    if response['status'] == 'error':
        return response, 403

    return response
