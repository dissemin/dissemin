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
from papers.models import Paper
from deposit.tests import ProtocolTest
from deposit.sword.protocol import SwordProtocol
from unittest import expectedFailure

class SwordProtocolTest(ProtocolTest):

    def setUp(self):
        super(SwordProtocolTest, self).setUp()
        self.repo.username = 'dspacedemo+submit@gmail.com'
        self.repo.password = 'dspace'
        self.repo.endpoint = 'http://demo.dspace.org/swordv2/servicedocument'
        self.repo.api_key = 'http://demo.dspace.org/swordv2/collection/10673/2'
        self.proto = SwordProtocol(self.repo)

    @expectedFailure
    def test_lncs(self):
        """
        Submit a paper from LNCS
        """
        p = Paper.create_by_doi('10.1007/978-3-662-47666-6_5')
        r = self.dry_deposit(p, abstract='this is a test abstract')
        self.assertEqual(r.status, 'faked')

