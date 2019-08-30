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
import os
import pytest

from mock import patch

from django.urls import reverse

from dissemin.settings import BASE_DIR
from papers.baremodels import BareName
from papers.models import OaiRecord
from papers.models import Paper
from papers.models import Researcher
from papers.doi import doi_to_url


@pytest.mark.usefixtures("load_test_data")
class TestDoai():
    def test_redirect_pdf(self, check_permanent_redirect):
        p = Paper.get_by_doi('10.1145/2767109.2767116')
        p.pdf_url = 'http://my.fantastic.repository/'
        p.save()
        check_permanent_redirect('paper-redirect-doi', kwargs={'doi':'10.1145/2767109.2767116'}, url=p.pdf_url)

    def test_404(self, check_status):
        check_status(404, 'paper-redirect-doi', kwargs={'doi':'10.1blabla'})

    def test_fallback(self, check_permanent_redirect):
        check_permanent_redirect('paper-redirect-doi', kwargs={'doi': '10.1385/1592597998'}, url=doi_to_url('10.1385/1592597998'))


@pytest.mark.usefixtures("load_test_data")
class TestInstitutionPages():

    def test_dept(self, check_url):
        check_url(200, self.d.url)
        check_url(200, self.di.url)

    def test_univ(self, check_url):
        check_url(200, self.i.url)


class TestMiscPages(object):
    """
    Tests various more or less static pages
    """

    def test_index(self, db, check_page):
        """
        Tests the start page, which fetches some data from the DB
        """
        check_page(200, 'index')


    @pytest.mark.parametrize('page', ['account_login', 'faq', 'partners', 'sources', 'tos'])
    def test_static(self, page, check_page):
        """
        Tests above static pages
        """
        check_page(200, page)


class TestPaperCSS():
    """
    Class that groups CSS tests for papers
    """
    def test_paper_css(self, css_validator):
        """
        Tests the css files
        """
        css_validator(os.path.join(BASE_DIR, 'papers', 'static', 'style'))


@pytest.mark.usefixtures("load_test_data")
class TestPaperPages():
    """
    Test class to test various paper related pages
    The tests could be improved / more explicit, because they rely on load_test_data, which loads a lot of things, but noone knows what.
    """

    def test_department_papers(self, check_page):
        check_page(200, 'department-papers', kwargs={'pk': self.di.pk})

    def test_invalid_doi(self, check_status):
        check_status(404, 'paper-doi', kwargs={'doi':'10.1blabla'})

    def test_invalid_orcid(self, check_status):
        check_status(404, 'researcher-by-orcid',  kwargs={'orcid': '0000-0002-2803-9724'})

    def test_invisible_paper(self, db, check_status):
        """
        If a paper is marked as invisible, then accessing it returns 404
        """
        p = Paper.create_by_doi('10.1007/978-3-642-14363-2_7')
        p.visible = False
        p.save()
        check_status(404, 'paper', kwargs={'pk': p.id, 'slug': p.slug})

    def test_journal(self, check_status):
        # TODO checkPage when logged in as superuser.
        # Move to publisher app?
        check_status(404, 'journal', kwargs={'journal': self.lncs.pk})

    def test_missing_info_in_pub(self, db, check_page):
        p = Paper.create_by_doi('10.1007/978-3-642-14363-2_7')
        check_page(200, 'paper', kwargs={'pk': p.id, 'slug': p.slug})

    def test_paper(self, check_page):
        for p in self.r3.papers:
            check_page(200, 'paper', kwargs={'pk': p.id, 'slug': p.slug})
            if p.is_orphan() and p.visible:
                print(p)
            assert p.is_orphan() == False

    def test_paper_by_doi(self, db, check_permanent_redirect):
        publi = OaiRecord.objects.filter(doi__isnull=False)[0]
        check_permanent_redirect('paper-doi', kwargs={'doi': publi.doi}, url=publi.about.url)

    def test_paper_by_doi_escaped(self, check_permanent_redirect):
        """
        Automatically unescape DOIs, for issue
        https://github.com/dissemin/dissemin/issues/517
        """
        paper = Paper.create_by_doi('10.1175/1520-0426(2003)020<0383%3ARCAACO>2.0.CO%3B2')
        paper.save()
        check_permanent_redirect(
            'paper-doi',
            kwargs={'doi':'10.1175%2F1520-0426%282003%29020%3C0383%3ARCAACO%3E2.0.CO%3B2'},
            url=paper.url,
        )

    def test_paper_by_doi_orphan(self, check_status):
        # This is the DOI for a book: enough data to create a Paper
        # object, but not enough to create an OaiRecord, so the paper
        # is orphan: this should return a 404
        check_status(404, 'paper-doi', kwargs={'doi': '10.1385/1592597998'})

    def test_paper_with_empty_slug(self, db, check_page):
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
        assert p.slug == ''
        check_page(200, 'paper', args=[p.pk, p.slug])

    def test_publisher_papers(self, check_status):
        # TODO checkPage when logged in as superuser.
        # Move to publisher app?
        check_status(404, 'publisher-papers', args=[self.acm.pk, self.acm.slug])

    def test_researcher(self, check_page):
        for r in [self.r1, self.r2, self.r3, self.r4]:
            check_page(200, 'researcher', kwargs={'researcher': r.pk, 'slug': r.slug})

    def test_researcher_blocked_orcid(self, check_status):
        check_status(404, 'researcher-by-orcid', kwargs={'orcid': '9999-9999-9999-9994'})

    def test_researcher_no_name(self, check_status):
        """
        This ORCID profile does not have a public name:
        """
        check_status(404, 'researcher-by-orcid', kwargs={'orcid': '0000-0002-6091-2701'})

    def test_researcher_not_visible(self, check_permanent_redirect):
        self.r1.visible = False
        self.r1.save()
        check_permanent_redirect('researcher', kwargs={'researcher': self.r1.pk, 'slug': self.r1.slug})

    def test_researcher_orcid(self, check_permanent_redirect):
        check_permanent_redirect('researcher-by-orcid', kwargs={'orcid': self.r4.orcid})

    def test_researcher_with_empty_slug(self, check_page):
        """
        Researchers may have names with characters that
        are all ignored by slugify.
        """
        r = Researcher.create_by_name('!@#', '$%^')
        assert r.slug == ''
        check_page(200, 'researcher', args=[r.pk, r.slug])

    def test_update_researcher_not_logged_in(self, check_status):
        check_status(302, 'refetch-researcher', kwargs={'pk':self.r4.id})

    def test_update_researcher_superuser(self, check_status, authenticated_client_su):
        """
        Superusers can refetch any researcher, yay!
        """
        from backend.tasks import fetch_everything_for_researcher
        with patch.object(fetch_everything_for_researcher, 'delay') as task_mock:
            check_status(302, 'refetch-researcher', kwargs={'pk':self.r4.id}, client=authenticated_client_su)

            task_mock.assert_called_once_with(pk=str(self.r4.id))

    def test_update_researcher_wrong_user(self, check_status, authenticated_client):
        """
        We currently don't allow any user to refresh any profile.
        Only superusers can do that. Maybe it's something we could reconsider though.
        """
        check_status(403, 'refetch-researcher', kwargs={'pk':self.r4.id}, client=authenticated_client)

    def test_visible_paper(self, check_page):
        """
        By default, a paper accessed with its pk and slug is visible
        """
        p = Paper.create_by_doi('10.1007/978-3-642-14363-2_7')
        check_page(200, 'paper', kwargs={'pk': p.id, 'slug': p.slug})


@pytest.mark.usefixtures('load_test_data', 'rebuild_index')
class TestSearchPages():
    """
    Tests concerning the search pages
    The tests could be improved / more explicit, because they rely on load_test_data, which loads a lot of things, but noone knows what.
    There could be more test cases
    """

    def test_search(self, check_page):
        check_page(200, 'search')

    def test_search_by_author(self, check_page):
        check_page(200, 'search', getargs={'authors': self.r3.name})


class TestTodoList():
    """
    Test concerning TodoListView
    """

    def test_login_required(self, check_status):
        """
        Login required
        """
        check_status(302, 'my-todolist')

    def test_todolist_view(self, check_html, authenticated_client, book_god_of_the_labyrinth):
        """
        Test of the to-do list view with items
        """
        book_god_of_the_labyrinth.todolist.add(authenticated_client.user)
        response = authenticated_client.get(reverse('my-todolist'))

        assert response.status_code == 200

        check_html(response)

        assert len(response.context['object_list']) == 1
        assert book_god_of_the_labyrinth.pk in [paper.pk for paper in response.context['object_list']]
        assert response.context['view'] == 'my-todolist'
        assert response.context['ajax_url'] == reverse('ajax-todolist')


# TODO TO BE TESTED

#        # Paper views
#        url(r'^mail_paper/(?P<pk>\d+)/$', views.mailPaperView, name='mail_paper'),
#        # Tasks, AJAX
#        url(r'^researcher/(?P<pk>\d+)/recluster/$', views.reclusterResearcher, name='recluster-researcher'),
#        # Annotations (to be deleted)
#        url(r'^annotations/$', views.AnnotationsView.as_view(), name='annotations'),
