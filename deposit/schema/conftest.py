import os
import pytest

from lxml import etree

@pytest.fixture(scope="class")
def dissemin_xsd_1_0():
    '''
    Loads dissemin xsd and prepares it as schema ready for validation.
    '''

    testdir = os.path.dirname(os.path.abspath(__file__))
    dissemin_xsd = etree.parse(os.path.join(testdir, 'dissemin_v1.0.xsd'))
    return etree.XMLSchema(dissemin_xsd)

@pytest.fixture
def dissemin_xml_1_0():
    '''
    Loads a dissemin xml document ready to be manipulated and be validated
    '''

    testdir = os.path.dirname(os.path.abspath(__file__))
    return etree.parse(os.path.join(testdir, 'fixtures', 'dissemin_v1.0.xml')).getroot()

