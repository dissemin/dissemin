import os
import pytest

from lxml import etree

from deposit.sword.protocol import SWORDMETSMODSProtocol


@pytest.fixture
def sword_mods_protocol(request, repository):
    """
    Creates a sword mods repository object
    """
    sword_mods_repository = repository.sword_mets_repository()
    request.cls.protocol = SWORDMETSMODSProtocol(sword_mods_repository)


@pytest.fixture()
def metadata_xml_dc():
    """
    Returns bibliographic metadata as lxml etree. Use this fixture if you just need some metadata in XML format and it's content is not important.
    """
    conftest_dir = os.path.dirname(os.path.abspath(__file__))
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(os.path.join(conftest_dir, 'test_data', 'dc_lesebibliothek_frauenzimmer.xml'), parser).getroot()


@pytest.fixture
def metadata_xml_mets():
    """
    Returns a mets formatted xml with some metadata in dmdSec
    """
    conftest_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(conftest_dir, 'test_data', 'mets_dc_lesebibliothek_frauenzimmer.xml'), 'r') as f:
        xml = f.read()
    return xml


@pytest.fixture(scope='session')
def mets_xsd():
    """
    Returns a mets xsd as schema ready to validate
    """
    return etree.XMLSchema(etree.parse("http://www.loc.gov/standards/mets/version112/mets.xsd"))


@pytest.fixture(scope="class")
def mods_3_7_xsd():
    '''
    Loads mods 3.7 xsd and prepares it as schema ready for validation.
    '''

    mods_xsd = etree.parse("http://www.loc.gov/standards/mods/v3/mods-3-7.xsd")
    return etree.XMLSchema(mods_xsd)



@pytest.fixture
def mock_get_xml_metadata(request, monkeypatch, metadata_xml_dc):
    """
    Mocks _get_xml_metadata so that it returns metadata and does not raise exception.
    """
    def _get_xml_metadata(*args, **kwargs):
        return metadata_xml_dc

    monkeypatch.setattr(request.cls.protocol, '_get_xml_metadata', _get_xml_metadata)


@pytest.fixture
def mock_get_deposit_result(request, monkeypatch):
    """
    Mocks _get_deposit_reult so that it returns ``None`` and does not raise exception.
    """
    def _get_deposit_result(*args, **kwargs):
        return None

    monkeypatch.setattr(request.cls.protocol, '_get_deposit_result', _get_deposit_result)
