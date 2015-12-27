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
import html5lib
from papers.utils import overescaped_re
from django.core.urlresolvers import reverse
from backend.tests import PrefilledTest
from backend.globals import get_ccf
from backend.crossref import CrossRefPaperSource
from backend.oai import OaiPaperSource
from papers.models import Publication

# TODO TO BE TESTED

#        # Paper views
#        url(r'^mail_paper/(?P<pk>\d+)/$', views.mailPaperView, name='mail_paper'),
#        url(r'^journal/(?P<journal>\d+)/$', views.searchView, name='journal'),
#        # Tasks, AJAX
#        url(r'^researcher/(?P<pk>\d+)/update/$', views.refetchResearcher, name='refetch-researcher'),
#        url(r'^researcher/(?P<pk>\d+)/recluster/$', views.reclusterResearcher, name='recluster-researcher'),
#        # Annotations (to be deleted)
#        url(r'^annotations/$', views.AnnotationsView.as_view(), name='annotations'),

class RenderingTest(PrefilledTest):
    def setUp(self):
        super(RenderingTest, self).setUp()
        self.client = django.test.Client()
        self.parser = html5lib.HTMLParser(strict=True)

    def checkHtml(self, resp):
        self.assertEqual(resp.status_code, 200)
        # Check that there are no overescaped HTML strings…
        self.assertEqual(overescaped_re.findall(resp.content), [])
        try:
            parsed = self.parser.parse(resp.content)
        except html5lib.html5parser.ParseError as e:
            print resp.content
            print e
            raise e

    def getPage(self, *args, **kwargs):
        urlargs = kwargs.copy()
        if 'getargs' in kwargs:
            del urlargs['getargs']
            return self.client.get(reverse(*args, **urlargs), kwargs['getargs'])
        return self.client.get(reverse(*args, **kwargs))

    def checkPage(self, *args, **kwargs):
        self.checkHtml(self.getPage(*args, **kwargs))

    def checkUrl(self, url):
        self.checkHtml(self.client.get(url))

class InstitutionPagesTest(RenderingTest):
    def test_dept(self):
        self.checkUrl(self.d.url)
        self.checkUrl(self.di.url)

    def test_univ(self):
        self.checkUrl(self.i.url)

class PaperPagesTest(RenderingTest):
    @classmethod
    def setUpClass(self):
        super(PaperPagesTest, self).setUpClass()
        ccf = get_ccf()
        crps = CrossRefPaperSource(ccf)
        oai = OaiPaperSource(ccf)
        crps.fetch(self.r3, incremental=True)
        oai.fetch(self.r3, incremental=True)

    def test_index(self):
        self.checkHtml(self.getPage('index'))
        
    def test_researcher(self):
        for r in [self.r1, self.r2, self.r3, self.r4]:
            self.checkPage('researcher', kwargs={'researcher':r.pk})
            self.checkUrl(self.r4.url)

    def test_researcher_orcid(self):
        self.checkPage('researcher-by-orcid', kwargs={'orcid':self.r4.orcid})

    # ampersands not escaped in django bootstrap pagination, https://github.com/jmcclell/django-bootstrap-pagination/issues/41
    @unittest.expectedFailure
    def test_search(self):
        self.checkPage('search')
        self.checkPage('search', getargs={'researcher':self.r3.pk})
        self.checkPage('search', getargs={'name':self.r3.name_id})
        # TODO more tests here

#        url(r'^my-profile', views.myProfileView, name='my-profile'),

    def test_paper(self):
        for a in self.r3.authors_by_year:
            self.checkPage('paper', kwargs={'pk':a.paper_id})
            if a.paper.is_orphan():
                print a.paper
            self.assertTrue(not a.paper.is_orphan())

    def test_paper_by_doi(self):
        publi = Publication.objects.all()[0]
        self.checkPage('paper-doi', kwargs={'doi':publi.doi})

