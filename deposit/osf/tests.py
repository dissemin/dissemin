#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
from __future__ import unicode_literals

# import unittest
# from mock import Mock

from papers.models import Paper
from deposit.models import Repository
from deposit.tests import ProtocolTest
from deposit.osf.protocol import OSFProtocol
from deposit.protocol import DepositError


class OSFProtocolTest(ProtocolTest):
    @classmethod
    def setUpClass(self):
        super(OSFProtocolTest, self).setUpClass()

        # Fill here the details of your test repository
        self.repo.api_key = 'eJMuNoeFvKTIC5A6POx1nrmsiQoMZqwh'
        self.repo.api_key += 'CgeEXwDgggYWDeR96Y9KbypgVGNuCY5r9qVgan'
        self.repo.endpoint = "https://test-api.osf.io/"

        # Now we set up the protocol for the tests
        self.proto = OSFProtocol(self.repo)

        # Fill here the details of the metadata form
        # for your repository
        data = {'onbehalfof': ''}
        self.form = self.proto.get_bound_form(data)
        self.form.is_valid()  # this validates our sample data

    def test_get_form_initial_data(self):
        paper = Paper.create_by_doi('10.1007/978-3-662-47666-6_5')
        record = paper.oairecords[0]
        record_value = "Supercalifragilisticexpialidocious."
        record.description = record_value
        record.save()

        self.proto.init_deposit(paper, self.user)
        data = self.proto.get_form_initial_data()
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get('abstract'), record_value)

    def test_create_tags(self):
        # Init deposit with default paper and user
        self.proto.init_deposit(self.p1, self.user)
        tags = " Witch,   Broom  ,  ,Bed "
        form = self.proto.get_bound_form(
                        {"license": "58fd62fcda3e2400012ca5d3",
                         "abstract": "Treguna Mekoides Trecorum Satis Dee.",
                         "tags": tags})

        self.assertTrue(form.is_valid())
        tags_list = self.proto.create_tags(form)
        self.assertEqual(tags_list, ['Witch', 'Broom', 'Bed'])

    def test_submit_deposit(self):
        paper = Paper.create_by_doi('10.1007/978-3-662-47666-6_5')

        request = self.dry_deposit(
                  paper,
                  license='58fd62fcda3e2400012ca5d3',
                  abstract='Salagadoola menchicka boola bibbidi-bobbidi-boo.',
                  tags='Pumpkin, Mouse, Godmother')

        self.assertEqualOrLog(request.status, 'published')

    def test_submit_deposit_nolicense(self):
        paper = Paper.create_by_doi('10.1007/978-3-662-47666-6_5')

        request = self.dry_deposit(
                  paper,
                  license='58fd62fcda3e2400012ca5cc',
                  abstract='Higitus Figitus Migitus Mum.',
                  tags='Sword, King, Wizard')

        self.assertEqualOrLog(request.status, 'published')

    def test_submit_deposit_notoken(self):
        no_token = Repository()
        no_token.api_key = None
        repo_without_token = OSFProtocol(no_token)

        data = {'onbehalfof': ''}
        repo_without_token.form = repo_without_token.get_bound_form(data)
        repo_without_token.form.is_valid()
        # paper = Paper.create_by_doi('10.1007/978-3-662-47666-6_5')
        # record = paper.oairecords[0]
        # record.description = "Itchita copita Melaka mystica."
        # record.keywords = "Salem, Black cat, Winnie"
        # record.save()
        # self.repo_without_token.init_deposit(paper, self.user)

        with self.assertRaises(DepositError):
            repo_without_token.submit_deposit(pdf=None, form=None)

    def test_form_with_no_subject(self):
        """
            Submit a preprint with no subject selected,
            which is a problem if we want to make it public.
        """
        paper = Paper.create_by_doi('10.1007/978-3-662-47666-6_5')
        self.proto.init_deposit(paper, self.user)

        # These are the initial data. No subject given.
        data = self.proto.get_form_initial_data()
        form_fields = {'licence': '563c1cf88c5e4a3877f9e965',
                       'abstract': 'This is a fake abstract.',
                       'tags': 'One, Two, Three, Four',
                       'subjects': []}
        data.update(form_fields)

        form = self.proto.get_bound_form(data)
        # self.assertFieldOutput(MultipleChoiceField,
        #                        {['584240da54be81056cecaca9']:['584240da54be81056cecaca9']},
        #                        {['']:['At least one subject is required.']})
        self.assertEqual(form.has_error('subjects', code=None), True)
        print(form.errors['subjects'])
        self.assertEqual(form.errors['subjects'],
                         ['At least one subject is required.'])
        self.assertFalse(form.is_valid())
