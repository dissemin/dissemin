import os
import pytest

from lxml import etree


@pytest.fixture
def dissemin_xml_1_0():
    '''
    Loads a dissemin xml document ready to be manipulated and be validated
    '''

    testdir = os.path.dirname(os.path.abspath(__file__))
    return etree.parse(os.path.join(testdir, 'test_data', 'dissemin_v1.0.xml')).getroot()

