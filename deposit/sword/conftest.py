import os
import pytest

from lxml import etree

from deposit.sword.protocol import SWORDMETSProtocol


@pytest.fixture()
def sword_mets_protocol(request, db, repository):
    """
    Creates a sowrd mets repository object
    """
    sword_mets_repository = repository.sword_mets_repository()
    request.cls.protocol = SWORDMETSProtocol(sword_mets_repository)


@pytest.fixture()
def metadata_xml_dc():
    """
    Returns bibliographic metadata as lxml etree. Use this fixture if you just need some metadata in XML format and it's content is not important.
    """
    conftest_dir = os.path.dirname(os.path.abspath(__file__))
    return etree.parse(os.path.join(conftest_dir, 'test_data', 'dc_lesebibliothek_frauenzimmer.xml')).getroot()


@pytest.fixture()
def mets_xsd():
    """
    Returns a mets xsd as schema ready to validate
    """
    conftest_dir = os.path.dirname(os.path.abspath(__file__))
    mets_xsd = etree.parse(os.path.join(conftest_dir, 'test_data', 'mets_1.12.xsd'))
    return etree.XMLSchema(mets_xsd)
