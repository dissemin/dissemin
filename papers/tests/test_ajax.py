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



import json
import pytest

from conftest import get_researcher_by_name
from django.contrib.auth.models import User
from django.urls import reverse
import django.test
from papers.models import Paper


# TODO TO BE TESTED
# urlpatterns = patterns('',
##    url(r'^annotate-paper-(?P<pk>\d+)-(?P<status>\d+)$', annotatePaper, name='ajax-annotatePaper'),
##    url(r'^delete-researcher-(?P<pk>\d+)$', deleteResearcher, name='ajax-delete-researcher'),
#    url(r'^add-researcher$', addResearcher, name='ajax-addResearcher'),
##    url(r'^harvesting-status-(?P<pk>\d+)$', harvestingStatus, name='ajax-harvestingStatus'),
#    url(r'^wait-for-consolidated-field$', waitForConsolidatedField, name='ajax-waitForConsolidatedField'),
#)


class TestTodoList():
    """
    Groups test for Ajax todo list function
    """

    @pytest.fixture(params=['ajax-todolist-add', 'ajax-todolist-remove'])
    def todolist_helper(self, request, monkeypatch, authenticated_client, book_god_of_the_labyrinth):
        """
        Helper to make AJAX requests and assertions on results
        """
        class MonkeypatchTodoList:
            """
            Helper class to monkeypatch for a Many2Many add/remove error
            """
            def add(self, *args, **kwargs):
                raise Exception("This is an anonymous exception")

            def remove(self, *args, **kwargs):
                raise Exception("This is an anonymous exception")


        def todolist_assert(data, status, add, remove, monkeypatched=False):
            """
            Make the POST request and does assertions
            """
            if request.param == 'ajax-todolist-add':
                expected_result= add
            else:
                expected_result = remove
                book_god_of_the_labyrinth.todolist.add(authenticated_client.user)

            if monkeypatched:
                monkeypatch.setattr(Paper, 'todolist', MonkeypatchTodoList() , False)

            response = authenticated_client.post(reverse(request.param), data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

            assert response.status_code == status
            json_resp = response.json()
            for key in ['success_msg', 'error_msg', 'data-action']:
                assert key in json_resp
            monkeypatch.undo()
            assert book_god_of_the_labyrinth.todolist.filter(pk=authenticated_client.user.pk).exists() == expected_result

        helper = {
            'asserts': todolist_assert,
            'paper_pk': book_god_of_the_labyrinth.pk
        }
        return helper


    def test_todo_list_success(self, todolist_helper):
        """
        Paper successfully added / removed from todolist
        """
        data = {
            'paper_pk': todolist_helper['paper_pk']
        }
        todolist_helper['asserts'](data, 200, True, False)


    def test_todo_list_no_paper_pk(self, todolist_helper):
        """
        No paper PK provided. Nothing happens
        """
        data = {
            'spam': 'eggs'
        }
        todolist_helper['asserts'](data, 400, False, True)


    def test_todo_list_no_paper_found(self, todolist_helper):
        """
        Paper PK not in DB. Nothing happens.
        """
        data = {
            'paper_pk': 'spanish inquisition'
        }
        todolist_helper['asserts'](data, 404, False, True)


    def test_todo_list_failed(self, todolist_helper, monkeypatch):
        """
        Problem with adding / removing paper from users todo list.
        """
        data = {
            'paper_pk': todolist_helper['paper_pk']
        }
        todolist_helper['asserts'](data, 500, False, True, monkeypatched=True)

    @pytest.mark.parametrize('url_name', ['ajax-todolist-add', 'ajax-todolist-remove'])
    def test_todo_list_unauthenticated(self, dissemin_base_client, url_name):
        """
        If client not logged in, expect 401
        """
        response = dissemin_base_client.post(reverse(url_name), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        assert response.status_code == 401


    @pytest.mark.parametrize('url_name', ['ajax-todolist-add', 'ajax-todolist-remove'])
    def test_todo_list_no_ajax(self, authenticated_client, url_name):
        """
        If client does not send XMLHttpRequest, send bad request
        """
        response = authenticated_client.post(reverse(url_name))
        assert response.status_code == 400


class JsonRenderingTest(django.test.TestCase):

    def setUp(self):
        self.client = django.test.Client()

    def checkJson(self, resp, expected_status=200):
        if resp.status_code != expected_status:
            print("Invalid status code %d, response was:\n%s" %
                (resp.status_code, resp.content))
        self.assertEqual(resp.status_code, expected_status)
        parsed = json.loads(resp.content.decode('utf-8'))
        return parsed

    def ajaxGet(self, *args, **kwargs):
        kwargs['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        kwargs['CONTENT_TYPE'] = 'application/json'
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
        if 'postkwargs' in urlargs:
            del urlargs['postkwargs']
        return self.ajaxPost(reverse(*args, **urlargs), kwargs['postargs'], **kwargs.get('postkwargs', {}))

@pytest.mark.usefixtures("load_test_data")
class PaperAjaxTest(JsonRenderingTest):

    def setUp(self):
        super(PaperAjaxTest, self).setUp()
        u = User.objects.create_user('terry', 'pit@mat.io', 'yo')
        u.save()
        self.r1 = get_researcher_by_name('Isabelle', 'Aujard')

    def test_researcher_papers(self):
        page = self.getPage('researcher',
                            kwargs={'researcher': self.r1.id,
                                    'slug': self.r1.slug})
        self.checkJson(page)

    @pytest.mark.usefixtures('mock_doi')
    def test_consolidate_paper(self):
        p = Paper.create_by_doi('10.1175/jas-d-15-0240.1')
        self.client.login(username='terry', password='yo')
        result = self.checkJson(self.getPage(
                'ajax-waitForConsolidatedField', getargs={
                    'field': 'abstract',
                    'id': p.id}))
        self.client.logout()
        self.assertTrue(result['success'])
        self.assertTrue(len(result['value']) > 10)

    @pytest.mark.usefixtures('mock_doi')
    def test_consolidate_elsevier_paper(self):
        p = Paper.create_by_doi('10.1016/0168-5597(91)90120-m')
        self.client.login(username='terry', password='yo')
        result = self.checkJson(self.getPage(
                'ajax-waitForConsolidatedField', getargs={
                    'field': 'abstract',
                    'id': p.id}))
        self.client.logout()
        self.assertTrue(result['success'])
        self.assertTrue(len(result['value']) > 10)


