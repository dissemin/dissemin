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




import datetime
import html5validator
import os
import pytest
import tempfile
from mock import patch

from django.urls import reverse
import django.test
from papers.baremodels import BareName
from papers.models import OaiRecord
from papers.models import Paper
from papers.models import Researcher
from papers.utils import overescaped_re
from django.contrib.auth.models import User
from papers.doi import doi_to_url


# TODO TO BE TESTED

#        # Paper views
#        url(r'^mail_paper/(?P<pk>\d+)/$', views.mailPaperView, name='mail_paper'),
#        # Tasks, AJAX
#        url(r'^researcher/(?P<pk>\d+)/recluster/$', views.reclusterResearcher, name='recluster-researcher'),
#        # Annotations (to be deleted)
#        url(r'^annotations/$', views.AnnotationsView.as_view(), name='annotations'),


class RenderingTest(django.test.TestCase):
    def setUp(self):
        super(RenderingTest, self).setUp()
        # Django test client does not set HTTP_HOST by default, therefore
        # having an empty request.META.HTTP_HOST variable which is an issue for
        # some tests (HTML validity of links URLs). We therefore force it to be
        # "localhost" in tests.
        self.client = django.test.Client(HTTP_HOST='localhost')
        self.validator = html5validator.Validator(
            errors_only=True,
            # Django Bootstrap DatetimePicker uses this extra attribute which
            # is considered invalid by W3C validator.
            ignore_re=['Attribute "dp_config" not allowed on element'],
        )

    def checkHtml(self, resp):
        self.assertEqual(resp.status_code, 200)
        # Check that there are no overescaped HTML strings…
        self.assertEqual(
            overescaped_re.findall(resp.content.decode('utf-8')),
            []
        )
        # Check HTML markup with W3C HTML5 validator
        fh = tempfile.NamedTemporaryFile(delete=False)
        fh.write(resp.content)
        fh.close()
        self.assertEqual(
            self.validator.validate([fh.name]),
            0
        )
        try:
            os.remove(fh.name)
        except OSError:
            pass

    def checkCss(self, directory):
        self.assertEqual(
            self.validator.validate([
                x
                for x in os.listdir(directory)
                if x.endswith('.css')
            ]),
            0
        )

    def getPage(self, *args, **kwargs):
        urlargs = kwargs.copy()
        if 'getargs' in kwargs:
            del urlargs['getargs']
            return self.client.get(reverse(*args, **urlargs), kwargs['getargs'])
        return self.client.get(reverse(*args, **kwargs))

    def checkPage(self, *args, **kwargs):
        # make sure there's no toolbar, as it may break the tests
        with self.settings(DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK':
                (lambda r: False)}):
            return self.checkHtml(self.getPage(*args, **kwargs))

    def checkPermanentRedirect(self, *args, **kwargs):
        target_url = kwargs.get('url')
        if target_url:
            del kwargs['url']
        response = self.getPage(*args, **kwargs)
        self.assertEqual(response.status_code, 301)
        if target_url:
            self.assertEqual(response.url, target_url)

    def checkTemporaryRedirect(self, *args, **kwargs):
        self.assertEqual(self.getPage(*args, **kwargs).status_code, 302)

    def checkForbidden(self, *args, **kwargs):
        self.assertEqual(self.getPage(*args, **kwargs).status_code, 403)

    def check404(self, *args, **kwargs):
        self.assertEqual(self.getPage(*args, **kwargs).status_code, 404)

    def checkUrl(self, url):
        self.checkHtml(self.client.get(url))

    def checkCSSFiles(self):
        self.checkCss('papers/static/style')

@pytest.mark.usefixtures("load_test_data")
class InstitutionPagesTest(RenderingTest):

    def test_dept(self):
        self.checkUrl(self.d.url)
        self.checkUrl(self.di.url)

    def test_univ(self):
        self.checkUrl(self.i.url)

@pytest.mark.usefixtures("load_test_data")
class PaperPagesTest(RenderingTest):

    def test_researcher(self):
        for r in [self.r1, self.r2, self.r3, self.r4]:
            self.checkPage('researcher', kwargs={
                           'researcher': r.pk, 'slug': r.slug})
            self.checkUrl(r.url)

    def test_researcher_orcid(self):
        self.checkPermanentRedirect(
            'researcher-by-orcid', kwargs={'orcid': self.r4.orcid})

    def test_update_researcher_not_logged_in(self):
        self.checkTemporaryRedirect(
            'refetch-researcher', kwargs={'pk':self.r4.id})

    def test_update_researcher_wrong_user(self):
        """
        We currently don't allow any user to refresh any profile.
        Only superusers can do that. Maybe it's something we could reconsider though.
        """
        User.objects.create_user('superuser', 'email@domain.com', 'mypass')
        self.client.login(username='superuser', password='mypass')
        self.checkForbidden(
            'refetch-researcher', kwargs={'pk':self.r4.id})

    def test_update_researcher_superuser(self):
        """
        Superusers can refetch any researcher, yay!
        """
        user = User.objects.create_user('superuser', 'email@domain.com', 'mypass')
        user.is_superuser = True
        user.save()
        self.client.login(username='superuser', password='mypass')

        from backend.tasks import fetch_everything_for_researcher
        with patch.object(fetch_everything_for_researcher, 'delay') as task_mock:
            self.checkTemporaryRedirect(
                'refetch-researcher', kwargs={'pk':self.r4.id})

            task_mock.assert_called_once_with(pk=str(self.r4.id))

    def test_researcher_no_name(self):
        # this ORCID profile does not have a public name:
        self.check404(
            'researcher-by-orcid', kwargs={'orcid': '0000-0002-6091-2701'})


    def test_researcher_with_empty_slug(self):
        """
        Researchers may have names with characters that
        are all ignored by slugify.
        """
        r = Researcher.create_by_name('!@#', '$%^')
        self.assertEqual(r.slug, '')
        self.checkPage('researcher', args=[r.pk, r.slug])

    def test_invalid_orcid(self):
        self.check404('researcher-by-orcid',
                      kwargs={'orcid': '0000-0002-2803-9724'})

    def test_researcher_blocked_orcid(self):
        self.check404('researcher-by-orcid',
                      kwargs={'orcid': '9999-9999-9999-9994'})

    def test_researcher_not_visible(self):
        self.r1.visible = False
        self.r1.save()
        self.checkPermanentRedirect('researcher', kwargs={'researcher': self.r1.pk, 'slug': self.r1.slug})

    def test_search_no_parameters(self):
        self.checkPage('search')

    def test_search_name(self):
        self.checkPage('search', getargs={'authors': self.r3.name})

    def test_department_papers(self):
        self.checkPage('department-papers', kwargs={'pk': self.di.pk})

    def test_missing_info_in_pub(self):
        p = Paper.create_by_doi('10.1007/978-3-642-14363-2_7')
        self.checkPage('paper', kwargs={'pk': p.id, 'slug': p.slug})

    def test_publisher_papers(self):
        # TODO checkPage when logged in as superuser.
        self.check404('publisher-papers', args=[self.acm.pk, self.acm.slug])

    def test_journal(self):
        # TODO checkPage when logged in as superuser.
        self.check404('journal', kwargs={'journal': self.lncs.pk})

    # ampersands not escaped in django bootstrap pagination,
    # https://github.com/jmcclell/django-bootstrap-pagination/issues/41

    def test_paper(self):
        for p in self.r3.papers:
            self.checkPage('paper', kwargs={'pk': p.id, 'slug': p.slug})
            if p.is_orphan() and p.visible:
                print(p)
            self.assertTrue(not p.is_orphan())

    def test_visible_paper(self):
        """
        By default, a paper accessed with its pk and slug is visible
        """
        p = Paper.create_by_doi('10.1007/978-3-642-14363-2_7')
        self.checkPage('paper', kwargs={'pk': p.id, 'slug': p.slug})

    def test_invisible_paper(self):
        """
        If a paper is marked as invisible, then accessing it returns 404
        """
        p = Paper.create_by_doi('10.1007/978-3-642-14363-2_7')
        p.visible = False
        p.save()
        self.check404('paper', kwargs={'pk': p.id, 'slug': p.slug})

    def test_paper_by_doi(self):
        publi = OaiRecord.objects.filter(doi__isnull=False)[0]
        self.checkPermanentRedirect('paper-doi', kwargs={'doi': publi.doi},
            url=publi.about.url)

    def test_paper_by_doi_escaped(self):
        """
        Automatically unescape DOIs, for issue
        https://github.com/dissemin/dissemin/issues/517
        """
        paper = Paper.create_by_doi('10.1175/1520-0426(2003)020<0383%3ARCAACO>2.0.CO%3B2')
        paper.save()
        self.checkPermanentRedirect('paper-doi',
            kwargs={'doi':'10.1175%2F1520-0426%282003%29020%3C0383%3ARCAACO%3E2.0.CO%3B2'},
            url=paper.url)

    def test_invalid_doi(self):
        self.check404('paper-doi', kwargs={'doi':'10.1blabla'})

    def test_paper_by_doi_orphan(self):
        # This is the DOI for a book: enough data to create a Paper
        # object, but not enough to create an OaiRecord, so the paper
        # is orphan: this should return a 404
        self.check404('paper-doi', kwargs={'doi': '10.1385/1592597998'})

    def test_paper_with_empty_slug(self):
        """
        Papers may have titles with characters that
        are all ignored by slugify.
        """
        p = Paper.get_or_create(
            '!@#$%^*()',
            [BareName.create('Jean', 'Saisrien')],
            datetime.date(2016, 7, 2))
        p.visible = True # Force paper to be visible even if it an orphan
        p.save()
        self.assertEqual(p.slug, '')
        self.checkPage('paper', args=[p.pk, p.slug])

@pytest.mark.usefixtures("load_test_data")
class DoaiTest(RenderingTest):
    def test_redirect_pdf(self):
        p = Paper.get_by_doi('10.1145/2767109.2767116')
        p.pdf_url = 'http://my.fantastic.repository/'
        p.save()
        self.checkPermanentRedirect('paper-redirect-doi', kwargs={'doi':'10.1145/2767109.2767116'},
            url=p.pdf_url)

    def test_404(self):
        self.check404('paper-redirect-doi', kwargs={'doi':'10.1blabla'})

    def test_fallback(self):
        self.checkPermanentRedirect('paper-redirect-doi', kwargs={'doi': '10.1385/1592597998'},
            url=doi_to_url('10.1385/1592597998'))

class MiscPagesTest(RenderingTest):

    def test_index(self):
        self.checkPage('index')

    def test_sources(self):
        self.checkPage('sources')

    def test_faq(self):
        self.checkPage('faq')

    def test_tos(self):
        self.checkPage('tos')

    def test_partners(self):
        self.checkPage('partners')

    def test_account_login(self):
        self.checkPage('account_login')


