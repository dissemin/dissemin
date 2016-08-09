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

import os
import unittest


from deposit.tests import lorem_ipsum
from deposit.tests import ProtocolTest
from deposit.zenodo.protocol import ZenodoProtocol


class ZenodoProtocolTest(ProtocolTest):

    @classmethod
    def setUpClass(self):
        if 'ZENODO_SANDBOX_API_KEY' not in os.environ:
            raise unittest.SkipTest(
                "Environment variable ZENODO_SANDBOX_API_KEY is undefined")
        super(ZenodoProtocolTest, self).setUpClass()
        self.repo.api_key = os.environ['ZENODO_SANDBOX_API_KEY']
        self.repo.endpoint = 'https://sandbox.zenodo.org/api/deposit/depositions'
        self.proto = ZenodoProtocol(self.repo)
        data = {}
        data['license'] = 'other-open'
        data['paper_id'] = self.p1.id
        data['abstract'] = lorem_ipsum
        self.form = self.proto.get_bound_form(data)
        self.form.is_valid()
