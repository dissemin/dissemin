import pytest
import responses

from lxml import etree
from requests.exceptions import RequestException
from zipfile import ZipFile

from deposit.sword.forms import SWORDMETSForm
from deposit.models import DDC
from deposit.models import License
from deposit.models import LicenseChooser
from deposit.protocol import DepositError
from deposit.sword.protocol import SWORDMETSProtocol
from deposit.tests.test_protocol import MetaTestProtocol

from papers.models import Paper
from papers.models import Researcher

userdata = [(None, None), ('vetinari', None), (None, 'psst')]

class MetaTestSWORDMETSProtocol(MetaTestProtocol):
    """
    This class contains some tests that every implemented SWORD protocol shall pass. The tests are not executed as members of this class, but of any subclass.
    """

    def test_get_mets(self, mets_xsd, metadata_xml_dc):
        """
        A test for creating mets from metadata
        """
        mets_xml = SWORDMETSProtocol._get_mets(metadata_xml_dc)
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

    @pytest.mark.parametrize('is_owned', [True, False])
    @pytest.mark.parametrize('license', [True, False])
    @pytest.mark.parametrize('orcid', [None, '2543-2454-2345-234X'])
    def test_get_xml_dissemin_metadata(self, db, monkeypatch, dissemin_xsd_1_0, user_isaac_newton, is_owned, license, orcid, upload_data):
        """
        Tests for dissemin metadata
        We happily override Paper.is_owned_by and use a non-valid orcid for isaac newton
        """
        monkeypatch.setattr(Paper, 'is_owned_by', lambda *args, **kwargs: is_owned)
        Researcher.create_by_name(first='isaac', last='newton', user=user_isaac_newton, orcid=orcid)
        if license:
            l = License.objects.get(uri='https://creativecommons.org/publicdomain/zero/1.0/')
            lc = LicenseChooser.objects.create(
                license=l,
                repository=self.protocol.repository,
                transmit_id='cc-zero-1.0'
            )

        self.protocol.paper = upload_data['paper']
        self.protocol.user = user_isaac_newton

        # Set POST data for form
        data = dict()

        if license:
            data['license'] = lc.pk
        data['email'] = 'isaac.newton@trinity-college.co.uk'

        form  = SWORDMETSForm(paper=self.protocol.paper, licenses=LicenseChooser.objects.by_repository(repository=self.protocol.repository), data=data)
        form.is_valid()

        xml = self.protocol._get_xml_dissemin_metadata(form)

        print("")
        print(etree.tostring(xml, pretty_print=True, encoding='utf-8', xml_declaration=True).decode())

        dissemin_xsd_1_0.assertValid(xml)


    @responses.activate
    def test_submit_deposit(self, blank_pdf_path, mock_get_xml_metadata, mock_get_deposit_result):
        """
        A test for submit deposit. We need to mock a function, that generates metadata depending on the metadata format that is created in a subclass.
        """
        # Mocking requests
        responses.add(responses.POST, self.protocol.repository.endpoint, status=201)

        assert self.protocol.submit_deposit(blank_pdf_path, None) == None


    @responses.activate
    def test_submit_deposit_server_error(self, blank_pdf_path, mock_get_xml_metadata):
        """
        A test where the repository is not available. Should raise ``requests.exceptions.RequestException``
        """
        responses.add(responses.POST, self.protocol.repository.endpoint, status=401)

        with pytest.raises(RequestException):
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


    @staticmethod
    def test_get_deposit_result():
        """
        Function must not be implemented in SWORDMETSProtocol
        """
        with pytest.raises(NotImplementedError):
            SWORDMETSProtocol._get_deposit_result(None)


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
