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

import os
import unittest
import requests
import requests_mock

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from papers.tests.test_ajax import JsonRenderingTest
from upload.models import THUMBNAIL_MAX_WIDTH
from upload.views import make_thumbnail
import wand.image as image


class ThumbnailTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(ThumbnailTest, cls).setUpClass()
        cls.testdir = os.path.dirname(os.path.abspath(__file__))

    def thumbnail(self, fname):
        with open(os.path.join(self.testdir, 'data', fname), 'rb') as f:
            pdf = f.read()
        ret = make_thumbnail(pdf)
        if ret is not None:
            pages, thumb = ret
            self.assertIsInstance(pages, int)
            return thumb

    def assertValidPng(self, png):
        img = image.Image(blob=png)
        self.assertEqual(img.format, 'PNG')
        self.assertTrue(img.width <= 2*THUMBNAIL_MAX_WIDTH)

    def test_valid_pdf(self):
        self.assertValidPng(self.thumbnail('blank.pdf'))

    def test_invalid_pdf(self):
        self.assertEqual(self.thumbnail('invalid.pdf'), None)

    def test_empty_pdf(self):
        self.assertEqual(self.thumbnail('empty.pdf'), None)

    def test_wrong_file_format(self):
        self.assertEqual(self.thumbnail('red-circle.png'), None)


class UploadTest(JsonRenderingTest):

    @classmethod
    def setUpClass(cls):
        super(UploadTest, cls).setUpClass()
        cls.testdir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(cls.testdir, 'data/blank.pdf'), 'rb') as blank_pdf:
            cls.blankpdf = blank_pdf.read()
        settings.MEDIA_ROOT = os.path.join(os.getcwd(), 'mediatest')
        User.objects.create_user('john', 'john@google.com', 'doe')

    def setUp(self):
        self.client.login(username='john', password='doe')

    def upload(self, fname):
        with open(os.path.join(self.testdir, 'data', fname), 'rb') as f:
            return self.ajaxPost(reverse('ajax-uploadFulltext'), {'upl': f})

    def download(self, url):
        return self.ajaxPost(reverse('ajax-downloadUrl'), {'url': url})

    def test_check_method(self):
        resp = self.ajaxGet(reverse('ajax-uploadFulltext'))
        self.assertEqual(resp.status_code, 405)

    def test_logged_out(self):
        self.client.logout()
        resp = self.upload('blank.pdf')
        self.assertEqual(resp.status_code, 302)

    def test_valid_upload(self):
        resp = self.upload('blank.pdf')
        if resp.status_code != 200:
            print("Invalid status code %d, response was:\n%s" %
                    (resp.status_code, resp.content))
        self.assertEqual(resp.status_code, 200)

    def test_invalid_format(self):
        resp = self.upload('invalid.pdf')
        if resp.status_code != 200:
            print(("Invalid status code %d, response was:\n%s" %
                    (resp.status_code, resp.content)))
        self.assertEqual(resp.status_code, 403)

    def test_download_nohttps(self):
        with requests_mock.mock() as http_mocker:
            http_mocker.get('http://my.awesome.http.repository/',
                content=self.blankpdf,
                headers={'content-type':'application/pdf'})

            resp = self.download('http://my.awesome.http.repository/')
            self.assertEqual(resp.status_code, 200)

    def test_download_https(self):
         with requests_mock.mock() as http_mocker:
            http_mocker.get('https://my.awesome.https.repository/',
                content=self.blankpdf,
                headers={'content-type':'application/pdf'})

            resp = self.download('https://my.awesome.https.repository/')
            self.assertEqual(resp.status_code, 200)

    def test_html_download(self):
        with requests_mock.mock() as http_mocker:
            http_mocker.get('http://my.awesome.http.repository/some_page.html',
                text='<html><head><title>Hello world</title></head><body></body></html>',
                headers={'content-type':'application/html'})

            resp = self.download('http://my.awesome.http.repository/some_page.html')
            self.assertEqual(resp.status_code, 403)

    def test_loggedout_download(self):
        self.client.logout()

        with requests_mock.mock() as http_mocker:
            http_mocker.get('https://my.awesome.https.repository/',
                content=self.blankpdf,
                headers={'content-type':'application/pdf'})

            resp = self.download('https://my.awesome.https.repository/')
            self.assertEqual(resp.status_code, 302)

    def test_invalid_url(self):
        self.download('ttp://dissem.in')

    def test_notfound_url(self):
        with requests_mock.mock() as http_mocker:
            http_mocker.get('http://my.awesome.http.repository/not_found.html',
                status_code=404,
                headers={'content-type':'application/html'})

            resp = self.download('http://my.awesome.http.repository/not_found.html')
            self.assertEqual(resp.status_code, 403)

    def test_timeout(self):
        with requests_mock.mock() as http_mocker:
            http_mocker.get('http://my.slow.repo/big.pdf', exc=requests.exceptions.ConnectTimeout)
            resp = self.download('http://my.slow.repo/big.pdf')
            self.assertEqual(resp.status_code, 403)
