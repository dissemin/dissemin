import pytest
import responses

from lxml import etree
from zipfile import ZipFile

from deposit.sword.forms import SWORDMETSForm
from deposit.models import DDC
from deposit.models import LicenseChooser
from deposit.protocol import DepositError
from deposit.protocol import DepositResult
from deposit.sword.protocol import SWORDMETSProtocol
from deposit.tests.test_protocol import MetaTestProtocol


userdata = [(None, None), ('vetinari', None), (None, 'psst')]

class MetaTestSWORDMETSProtocol(MetaTestProtocol):
    """
    This class contains some tests that every implemented SWORD protocol shall pass. The tests are not executed as members of this class, but of any subclass.
    """

    def test_get_deposit_result(self):
        """
        This test the creation of a DepositResult based on the information from a SWORD response.
        """
        identifier = '8128'
        splash_url = "https://repository.dissem.in/item/{}".format(identifier)
        response = '''<?xml version="1.0" encoding="utf-8" ?>
            <entry xmlns="http://www.w3.org/2005/Atom" xmlns:sword="http://purl.org/net/sword/">
                <sword:originalDeposit href="''' + splash_url + '''">
                    <sword:depositedOn/>
                    <sword:depositedBy>dissemin</sword:depositedBy>
                </sword:originalDeposit>
            </entry>'''

        dr = self.protocol._get_deposit_result(response)

        assert isinstance(dr, DepositResult)
        assert dr.identifier == identifier
        assert dr.splash_url == splash_url
        assert dr.status == 'pending'


    def test_get_deposit_result_invalid_xml(self):
        """
        If there's invalid XML, we expect a DepositError
        """
        response = "This is no XML"

        with pytest.raises(DepositError):
            self.protocol._get_deposit_result(response)


    @pytest.mark.parametrize(
        'response', [
            '''<?xml version="1.0" encoding="utf-8" ?>
                <entry xmlns="http://www.w3.org/2005/Atom" xmlns:sword="http://purl.org/net/sword/">
                    <sword:originalDeposit>
                        <sword:depositedOn/>
                        <sword:depositedBy>dissemin</sword:depositedBy>
                    </sword:originalDeposit>
                </entry>''',
            '''<?xml version="1.0" encoding="utf-8" ?>
                <entry xmlns="http://www.w3.org/2005/Atom" xmlns:sword="http://purl.org/net/sword/">
                <sword:spam>Spanish Inquisition</sword:spam>
                </entry>''']
    )
    def test_get_deposit_result_no_splash_url(self, response):
        """
        If the splash url cannot be found, splash_url and identifier must be ``None``.
        """
        dr = self.protocol._get_deposit_result(response)

        assert dr.identifier == None
        assert dr.splash_url == None
        assert dr.status == 'pending'
 

    def test_get_mets(self, mets_xsd, metadata_xml_dc, dissemin_xml_1_0):
        """
        A test for creating mets from metadata
        """
        mets_xml = SWORDMETSProtocol._get_mets(metadata_xml_dc, dissemin_xml_1_0)
        # Because of the xml declaration we have to convert to a bytes object
        mets_xsd.assertValid(etree.fromstring(bytes(mets_xml, encoding='utf-8')))


    def test_get_mets_integration(self, mets_xsd, depositing_user, upload_data, ddc, license_chooser):
        """
        Integration test running all possible metadata cases and validating against mets schema
        """
        self.protocol.paper = upload_data['paper']
        self.protocol.user = depositing_user

        # Set POST data for form
        data = dict()
        data['email'] = depositing_user.email
        if upload_data['oairecord'].description is not None:
            data['abstract'] = upload_data['oairecord'].description
        else:
            data['abstract'] = upload_data['abstract']

        if ddc is not None:
            data['ddc'] = [ddc for ddc in DDC.objects.filter(number__in=upload_data['ddc'])]

        if license_chooser:
            data['license'] = license_chooser.pk
        licenses = LicenseChooser.objects.by_repository(repository=self.protocol.repository)

        form = SWORDMETSForm(paper=self.protocol.paper, ddcs=ddc, licenses=licenses, data=data)
        form.is_valid()

        dissemin_xml = self.protocol._get_xml_dissemin_metadata(form)
        metadata_xml = self.protocol._get_xml_metadata(form)
        mets_xml = self.protocol._get_mets(dissemin_xml, metadata_xml)
        
        # Because of the xml declaration we have to convert to a bytes object
        mets_xsd.assertValid(etree.fromstring(bytes(mets_xml, encoding='utf-8')))


    def test_get_mets_container(self, blank_pdf_path, metadata_xml_mets):
        """
        A test for creating a mets container
        """
        s = SWORDMETSProtocol._get_mets_container(blank_pdf_path, metadata_xml_mets)
        with ZipFile(s, 'r') as zip_file:
            files = zip_file.namelist()
            for filename in ['mets.xml', 'document.pdf']:
                assert filename in files
            assert not zip_file.testzip()


    @pytest.mark.parametrize('oairecord', ['journal-article_a_female_signal_reflects_mhc_genotype_in_a_social_primate', 'book_god_of_the_labyrinth'])
    def test_get_xml_dissemin_metadata(self, db, monkeypatch_paper_is_owned, dissemin_xsd_1_0, depositing_user, license_chooser, load_json, oairecord):
        """
        Tests for dissemin metadata
        """
        upload_data = load_json.load_upload(oairecord)
        self.protocol.paper = upload_data['paper']
        self.protocol.user = depositing_user

        # Set POST data for form
        data = dict()

        if license_chooser:
            data['license'] = license_chooser.pk
        data['email'] = depositing_user.email

        form  = SWORDMETSForm(
            paper=self.protocol.paper,
            licenses=LicenseChooser.objects.by_repository(repository=self.protocol.repository),
            data=data
        )
        form.is_valid()

        xml = self.protocol._get_xml_dissemin_metadata(form)

        # When using pytest -s, show resulting xml
        print("")
        print(etree.tostring(xml, pretty_print=True, encoding='utf-8', xml_declaration=True).decode())

        dissemin_xsd_1_0.assertValid(xml)


    @responses.activate
    def test_submit_deposit(self, blank_pdf_path, monkeypatch_metadata_creation, monkeypatch_get_deposit_result):
        """
        A test for submit deposit.
        """
        # Mocking requests
        responses.add(responses.POST, self.protocol.repository.endpoint, status=201)

        assert isinstance(self.protocol.submit_deposit(blank_pdf_path, None), DepositResult)


    @responses.activate
    def test_submit_deposit_server_error(self, blank_pdf_path, monkeypatch_metadata_creation):
        """
        A test where the repository is not available. Should raise ``DepositError``
        """
        responses.add(responses.POST, self.protocol.repository.endpoint, status=401)

        with pytest.raises(DepositError):
            self.protocol.submit_deposit(blank_pdf_path, None)


    @pytest.mark.parametrize('username,password', userdata)
    def test_submit_deposit_login_missing(self, username, password):
        """
        If username or password are missing, an exception must be raised.
        """
        p = self.protocol 
        p.repository.username = username
        p.repository.password = password
        p.repository.save()
        with pytest.raises(DepositError):
            p.submit_deposit(None, None)


class TestSWORDMETSProtocolNotImplemented():
    """
    Tests that certain functions must not be implemented in SWORDMETSProtocol
    """
    @staticmethod
    def test_get_xml_metadata():
        """
        Function must not be implemented in SWORDMETSProtocol
        """
        with pytest.raises(NotImplementedError):
            SWORDMETSProtocol._get_xml_metadata(None)


@pytest.mark.usefixtures('sword_mods_protocol')
class TestSWORDSMETSMODSProtocol(MetaTestSWORDMETSProtocol):
    """
    A test class for named protocol
    """

    def deposit(self):
        """
        Manages publication, form and mocking
        """
        pass


    def test_str(self):
        """
        Tests the string output of class and object
        """
        assert self.protocol.__str__() == "SWORD Protocol (MODS)"


    def test_get_xml_metadata(self, mods_3_7_xsd, ddc, upload_data):
        """
        Validates against mods 3.7 schema
        """
        self.protocol.paper = upload_data['paper']

        # Set POST data for form
        data = dict()
        if upload_data['oairecord'].description is not None:
            data['abstract'] = upload_data['oairecord'].description
        else:
            data['abstract'] = upload_data['abstract']

        if ddc is not None:
            data['ddc'] = [ddc for ddc in DDC.objects.filter(number__in=upload_data['ddc'])]

        form = SWORDMETSForm(paper=self.protocol.paper, ddcs=ddc, data=data)
        form.is_valid()
        xml = self.protocol._get_xml_metadata(form)
        
        # When using pytest -s, show resulting xml
        print("")
        print(etree.tostring(xml, pretty_print=True, encoding='utf-8', xml_declaration=True).decode())

        mods_3_7_xsd.assertValid(xml)
