import pytest
import responses

from lxml import etree
from requests.exceptions import RequestException
from zipfile import ZipFile

from deposit.protocol import DepositError
from deposit.sword.protocol import SWORDMETSProtocol

userdata = [(None, None), ('vetinari', None), (None, 'psst')]

@pytest.mark.usefixtures('sword_mets_protocol')
class TestSWORDMETSProtocol(object):
    """
    A test class for named protocol
    """

    def test_str(self):
        """
        Tests the string output of class and object
        """
        assert self.protocol.__str__() == "SOWRD Protocol (METS)"


    def test_get_mets(self, mets_xsd, metadata_xml_dc):
        """
        A test for creating mets from metadata
        """
        mets_xml = SWORDMETSProtocol._get_mets(metadata_xml_dc)
        # Because of the xml declaration we have to convert to a bytes object
        mets_xsd.assertValid(etree.fromstring(bytes(mets_xml, encoding='utf-8')))


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


        
