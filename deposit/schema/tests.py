import os
import pytest

from lxml import etree

@pytest.mark.usefixtures('dissemin_xsd_1_0')
class TestDisseminXSD(object):
    '''
    Tests for the Dissemin XSD scheme. Validates against w3c xml schema
    '''

    def test_validate_xsd(self):
        '''
        Validates dissemin xml schema against xml schema
        '''
        xmlschema = etree.XMLSchema(etree.parse("http://www.w3.org/2001/XMLSchema.xsd"))
        testdir = os.path.dirname(os.path.abspath(__file__))
        dissemin_xsd = etree.parse(os.path.join(testdir, 'dissemin_v1.0.xsd'))

        xmlschema.assertValid(dissemin_xsd)


@pytest.mark.usefixtures('dissemin_xml_1_0', 'dissemin_xsd_1_0')
class TestDisseminXML_1_0(object):
    '''
    Validates XML against XSD to make sure that XSD validates as intended.
    '''

    def test_all_elements(self):
        '''
        Tests if the document with all elements and attributes is valid.
        '''

        self.dissemin_schema.assertValid(self.dissemin_xml)
    
    def test_optional_fields(self):
        '''
        The following elements are optional: orcid, isContributor, identicalInstitution, licenseURI, licenseShortName
        '''

        for i in range(3):
            self.dissemin_xml[0].remove(self.dissemin_xml[0][4])
        for i in range(2):
            self.dissemin_xml[1][0].remove(self.dissemin_xml[1][0][1])
        self.dissemin_schema.assertValid(self.dissemin_xml)


