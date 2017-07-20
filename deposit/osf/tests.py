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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
from __future__ import unicode_literals

# import unittest
# from mock import Mock

from papers.models import Paper
from deposit.tests import ProtocolTest
from deposit.osf.protocol import OSFProtocol
from deposit.forms import FormWithAbstract
from deposit.osf.forms import OSFForm
# lorem_ipsum contains a sample abstract you can reuse in your test case

class OSFProtocolTest(ProtocolTest):
    @classmethod
    def setUpClass(self):
        # if ''
        super(OSFProtocolTest, self).setUpClass()

        # Fill here the details of your test repository
        self.repo.username = ''
        self.repo.password = ''
        self.repo.endpoint = ''

        # Now we set up the protocol for the tests
        self.proto = OSFProtocol(self.repo)

        # Fill here the details of the metadata form
        # for your repository
        data = {'onbehalfof': ''}
        self.form = self.proto.get_bound_form(data)
        self.form.is_valid() # this validates our sample data

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
        tags = " One,   Two  ,  ,Three "
        form = self.proto.get_bound_form(
                        {"license": "58fd62fcda3e2400012ca5d3",
                         "abstract": "Supercalifragilisticexpialidocious.",
                         "tags": tags})

        self.assertTrue(form.is_valid())
        tags_list = self.proto.create_tags(form)
        self.assertEqual(tags_list, ['Un', 'Deux', 'Trois'])

    def test_submit_deposit(self):
        paper = Paper.create_by_doi('10.1007/978-3-662-47666-6_5')
        # record = paper.oairecords[0]
        # record_value = "Salagadoola menchicka boola bibbidi-bobbidi-boo."
        # tags_value = "One, Two, Three"
        # record_description = record_value
        # record_keywords = tags_value
        request = self.dry_deposit(paper,
                  license='58fd62fcda3e2400012ca5d3',
                  abstract='Salagadoola menchicka boola bibbidi-bobbidi-boo.',
                  tags='One, Two, Three')
        self.assertEqualOrLog(request.status, 'success')


