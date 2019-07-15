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

from datetime import date
from io import BytesIO
import unittest
import django.test
import pytest
import os

from deposit.models import License
from deposit.models import LicenseChooser
from deposit.protocol import DepositResult
from deposit.protocol import RepositoryProtocol
from deposit.registry import protocol_registry
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.forms import Form
from django.test.utils import override_settings
from papers.models import OaiSource
from papers.models import Paper
from deposit.tasks import refresh_deposit_statuses


class MetaTestProtocol():
    """
    This class contains some tests that every implemented protocol shall pass. The tests are not executed as members of this class, but of any subclass.
    """

    def deposit(self):
        """
        Replace this function in your testsubclass with suitable assert statements and so on.
        """
        raise NotImplementedError("This function must be overriden by any subclass")


    def test_deposit(self):
        """
        Tests the deposition. This function calls :meth:`deposit` unless it's not a member of a subclass.
        Do not override this function. Please override :meth:`deposit`.
        """
        self.deposit()


    def test_deposit_page(self, rendering_authenticated_client, rendering_get_page, book_god_of_the_labyrinth):
        """
        Test the deposit page for HTTP Response 200
        """
        r = rendering_get_page(rendering_authenticated_client, 'upload_paper', kwargs={'pk': book_god_of_the_labyrinth.pk})
        assert r.status_code == 200


    def test_get_form_return_type(self, user_isaac_newton, book_god_of_the_labyrinth):
        """
        Return type of get_form shall by a form
        """
        self.protocol.init_deposit(user_isaac_newton, book_god_of_the_labyrinth)
        form = self.protocol.get_form()
        assert isinstance(form, Form)


    def test_init_deposit_type(self, user_isaac_newton, book_god_of_the_labyrinth):
        """
        init_deposit shall return a bool
        """
        retval = self.protocol.init_deposit(user_isaac_newton, book_god_of_the_labyrinth)
        assert type(retval) == bool


    def test_get_licenses(self, db):
        """
        Function should return a queryset of of length > 1 of  LicenseChoosers if LicenseChoosers are choosen
        """
        for uri in ['https://creativecommons.org/publicdomain/zero/1.0/', 'https://creativecommons.org/licenses/by/4.0/', 'http://creativecommons.org/licenses/by-nd/4.0/']:
            license = License.objects.get(uri=uri)
            LicenseChooser.objects.create(
                license=license,
                repository=self.protocol.repository,
            )

        assert len(self.protocol._get_licenses()) == 3


    def test_get_licenses_none(self):
        """
        Function should return none if no LicenseChooser selected for repository
        """
        assert self.protocol._get_licenses() == None


    def test_protocol_identifier(self):
        """
        Identifier should exist
        """
        assert len(self.protocol.protocol_identifier()) > 1




# 1x1 px image used as default logo for the repository
simple_png_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x07tIME\x07\xdf\n\x12\x0c+\x19\x84\x1d/"\x00\x00\x00\x19tEXtComment\x00Created with GIMPW\x81\x0e\x17\x00\x00\x00\x0cIDAT\x08\xd7c\xa8\xa9\xa9\x01\x00\x02\xec\x01u\x90\x90\x1eL\x00\x00\x00\x00IEND\xaeB`\x82'

class DepositTest(django.test.TestCase):
    def test_refresh_deposit_statuses(self):
        # TODO: set up some DepositRecords + repository and protocol, to
        # so that this task actually does something
        refresh_deposit_statuses()

@pytest.mark.usefixtures("load_test_data")
class ProtocolTest(django.test.TestCase):
    """
    Set of generic tests that any protocol should pass.
    Note: This class is going to deprecated and is no longer maintained.
    """

    def __init__(self, *args, **kwargs):
        super(ProtocolTest, self).__init__(*args, **kwargs)

    @override_settings(MEDIA_ROOT='mediatest/')
    def setUp(self):
        if type(self) is ProtocolTest:
            raise unittest.SkipTest("Base test")
        self.p1 = Paper.get_or_create(
                "This is a test paper",
                [self.r1.name, self.r2.name, self.r4.name],
                date(year=2014, month=2, day=15))

        self.username = 'mydepositinguser'
        self.password = 'supersecret'
        self.user = User.objects.create_user(username=self.username, email="my@email.com", password=self.password)
        self.testdir = os.path.dirname(os.path.abspath(__file__))
        self.pdfpath = os.path.join(self.testdir, 'data/blank.pdf')

    def setUpForProtocol(self, protocol_class, repository):

        self.oaisource, _ = OaiSource.objects.get_or_create(
            identifier='deposit_oaisource',
            name='Repository OAI source',
            default_pubtype='preprint')
        logo = InMemoryUploadedFile(
                BytesIO(simple_png_image),
                None, 'logo.png',
                'image/png', len(simple_png_image), None, None)
        self.repo = repository
        self.repo.oaisource = self.oaisource
        self.repo.logo = logo
        if not self.repo.description:
            self.repo.description = 'brsuatiercs'
        if not self.repo.name:
            self.repo.name = 'Test Repository'
        self.repo.protocol = protocol_class.__name__
        self.repo.save()
        protocol_registry.register(protocol_class)
        self.proto = protocol_class(self.repo)
        self.form = None


    def test_protocol_identifier(self):
        self.assertTrue(len(self.proto.protocol_identifier()) > 1)

    def test_init_deposit(self):
        retval = self.proto.init_deposit(self.p1, self.user)
        self.assertIs(type(retval), bool)

    def test_get_form_return_type(self):
        self.proto.init_deposit(self.p1, self.user)
        retval = self.proto.get_form()
        self.assertIsInstance(retval, Form)

    def test_deposit_page(self):
        self.assertEqual(self.user.username, self.username)
        self.assertTrue(self.client.login(username=self.username, password=self.password))
        r = self.getPage('upload_paper', kwargs={'pk': self.p1.pk})
        self.assertEqual(r.status_code, 200)

    def dry_deposit(self, paper, **form_fields):
        """
        This is not a test by itself - it's a method
        subclasses can call to create a fake deposit
        (if the protocol supports it!)
        """
        return self.deposit(paper, dry_run=True, **form_fields)

    def deposit(self, paper, dry_run=False, **form_fields):
        enabled = self.proto.init_deposit(paper, self.user)
        self.assertTrue(enabled)

        licenses = LicenseChooser.objects.by_repository(repository=self.repo)
        args = self.proto.get_form_initial_data(licenses=licenses)
        args.update(form_fields)
        # The forms needs the pk of LicenceChooser object
        args['license'] = self.lc.pk

        form = self.proto.get_bound_form(args)
        if not form.is_valid():
            print(form.errors)
        self.assertTrue(form.is_valid())
        pdf = self.pdfpath
        deposit_result = self.proto.submit_deposit_wrapper(pdf,
                                                           form, dry_run=dry_run)
        self.assertIsInstance(deposit_result, DepositResult)
        self.assertIsInstance(deposit_result.additional_info, list)
        for i in deposit_result.additional_info:
            self.assertNotEqual(i.get('label'), None)
            self.assertNotEqual(i.get('value'), None)
        return deposit_result

    def assertEqualOrLog(self, a, b):
        """
        Same as assertEqual but prints logs before failing
        if the two quantities are not equal.
        """
        if a != b:
            print(self.proto._logs)
        self.assertEqual(a, b)

class ProtocolRegistryTest(django.test.TestCase):
    def test_get(self):
        c = protocol_registry.get('ZenodoProtocol')
        self.assertTrue(issubclass(c, RepositoryProtocol))

