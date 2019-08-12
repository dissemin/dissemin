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

from dissemin.settings import BASE_DIR


class TestDepositCSS():
    """
    Class that groups CSS tests for upload
    """
    def test_deposit_css(self, css_validator):
        """
        Tests the css files
        """
        css_validator(os.path.join(BASE_DIR, 'deposit', 'static', 'css'))


class TestDepositPages():

    def test_start_deposit_unauthenticated(self, book_god_of_the_labyrinth, check_status):
        paper = book_god_of_the_labyrinth
        check_status(302, 'upload_paper', kwargs={'pk': paper.pk})

    def test_start_deposit_authenticated(self, book_god_of_the_labyrinth, authenticated_client, check_page):
        paper = book_god_of_the_labyrinth
        check_page(200, 'upload_paper', kwargs={'pk': paper.pk}, client=authenticated_client)
