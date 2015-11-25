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
from papers.testajax import JsonRenderingTest
from papers.models import Paper

class PaperApiTest(JsonRenderingTest):
    @classmethod
    def setUpClass(self):
        super(PaperApiTest, self).setUpClass()
        ccf = get_ccf()
        crps = CrossRefPaperSource(ccf)
        oai = OaiPaperSource(ccf)
        crps.fetch(self.r3, incremental=True)
        oai.fetch(self.r3, incremental=True)

    def test_valid_paper(self):
        p = self.r3.author_set.first().paper
        parsed = self.checkJson(self.getPage('api-paper', args=[p.pk]))

        

