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

import os
import pytest

from django.contrib.auth.models import User

from dissemin.settings import BASE_DIR
from papers.tests.test_pages import RenderingTest


class TestDepositCSS():
    """
    Class that groups CSS tests for upload
    """
    def test_deposit_css(self, css_validator):
        """
        Tests the css files
        """
        css_validator(os.path.join(BASE_DIR, 'deposit', 'static', 'css'))


@pytest.mark.usefixtures("load_test_data")
class DepositPagesTest(RenderingTest):

    @classmethod
    def setUpClass(self):
        super(DepositPagesTest, self).setUpClass()

    def test_start_deposit_unauthenticated(self):
        paper = self.r3.papers[0]
        r = self.getPage('upload_paper', kwargs={'pk': paper.pk})
        self.assertEqual(r.status_code, 302)

    def test_start_deposit_authenticated(self):
        paper = self.r3.papers[0]
        User.objects.create_user('superuser', 'email@domain.com', 'mypass')
        self.client.login(username='superuser', password='mypass')
        self.checkPage('upload_paper', kwargs={'pk': paper.pk})
