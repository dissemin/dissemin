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

from django.test import TestCase
from backend.romeo import *
from papers.testpages import RenderingTest

class JournalPageTest(RenderingTest):

    def test_escaping(self):
        # issue #115
        journal = fetch_journal({'issn':'1309-534X'})
        # Small hack to make the journal appear in the publisher's journal list
        journal.update_stats()
        journal.stats.num_tot = 1
        journal.stats.save()
        r = self.getPage('publisher', kwargs={'pk':journal.publisher_id})
        print r.content
        self.checkHtml(r)

