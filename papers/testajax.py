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

import unittest
import django.test
import json
from django.core.urlresolvers import reverse
from backend.tests import PrefilledTest
from backend.globals import get_ccf
from backend.crossref import CrossRefPaperSource
from backend.oai import OaiPaperSource

# TODO TO BE TESTED
#urlpatterns = patterns('',
##    url(r'^annotate-paper-(?P<pk>\d+)-(?P<status>\d+)$', annotatePaper, name='ajax-annotatePaper'),
##    url(r'^delete-researcher-(?P<pk>\d+)$', deleteResearcher, name='ajax-deleteResearcher'),
##    url(r'^change-department$', changeDepartment, name='ajax-changeDepartment'),
##    url(r'^change-paper$', changePaper, name='ajax-changePaper'),
##    url(r'^change-researcher$', changeResearcher, name='ajax-changeResearcher'),
##    url(r'^change-author$', changeAuthor, name='ajax-changeAuthor'),
#    url(r'^add-researcher$', addResearcher, name='ajax-addResearcher'),
#    url(r'^new-unaffiliated-researcher$', newUnaffiliatedResearcher, name='ajax-newUnaffiliatedResearcher'),
#    url(r'^change-publisher-status$', changePublisherStatus, name='ajax-changePublisherStatus'),
##    url(r'^harvesting-status-(?P<pk>\d+)$', harvestingStatus, name='ajax-harvestingStatus'),
#    url(r'^wait-for-consolidated-field$', waitForConsolidatedField, name='ajax-waitForConsolidatedField'),
#)

class JsonRenderingTest(PrefilledTest):
    @classmethod
    def setUpClass(self):
        super(JsonRenderingTest, self).setUpClass()
        self.client = django.test.Client()

    def checkJson(self, resp, expected_status=200):
        self.assertEqual(resp.status_code, expected_status)
        parsed = json.loads(resp.content)
        return parsed

    def ajaxGet(self, *args, **kwargs):
        kwargs['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        return self.client.get(*args, **kwargs)

    def ajaxPost(self, *args, **kwargs):
        kwargs['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        return self.client.post(*args, **kwargs)

    def getPage(self, *args, **kwargs):
        urlargs = kwargs.copy()
        if 'getargs' in kwargs:
            del urlargs['getargs']
            return self.ajaxGet(reverse(*args, **urlargs), kwargs['getargs'])
        return self.ajaxGet(reverse(*args, **kwargs))

    def postPage(self, *args, **kwargs):
        urlargs = kwargs.copy()
        del urlargs['postargs']
        return self.ajaxPost(reverse(*args, **urlargs), kwargs['postargs'])


class PaperAjaxTest(JsonRenderingTest):
    @classmethod
    def setUpClass(self):
        super(PaperAjaxTest, self).setUpClass()
        ccf = get_ccf()
        crps = CrossRefPaperSource(ccf)
        oai = OaiPaperSource(ccf)
        crps.fetch(self.r3, incremental=True)
        oai.fetch(self.r3, incremental=True)

    def test_valid_search(self):
        for args in [
            {'first':'John','last':'Doe'},
            ]:
            parsed = self.checkJson(self.postPage('ajax-newUnaffiliatedResearcher',
                postargs=args))
            self.assertTrue(len(parsed) > 0)

    def test_invalid_search(self):
        for args in [
            {'orcid':'0000-0002-8435-1137'},
            {'first':'John'},
            {'last':'Doe'},
            {},
            ]:
            parsed = self.checkJson(self.postPage('ajax-newUnaffiliatedResearcher',
                postargs=args), 403)
            self.assertTrue(len(parsed) > 0)

        

