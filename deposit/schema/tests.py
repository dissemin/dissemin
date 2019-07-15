import os

from lxml import etree

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


class TestDisseminXML_1_0(object):
    '''
    Validates XML against XSD to make sure that XSD validates as intended.
    '''

    @staticmethod
    def test_all_elements(dissemin_xml_1_0, dissemin_xsd_1_0):
        '''
        Tests if the document with all elements and attributes is valid.
        '''

        dissemin_xsd_1_0.assertValid(dissemin_xml_1_0)
    

    @staticmethod
    def test_optional_fields(dissemin_xml_1_0, dissemin_xsd_1_0):
        '''
        The following elements are optional: orcid, isContributor, identicalInstitution, license, romeoId
        '''

        for i in range(3):
            dissemin_xml_1_0[0].remove(dissemin_xml_1_0[0][4])
        dissemin_xml_1_0[1].remove(dissemin_xml_1_0[1][0])
        dissemin_xml_1_0[1].remove(dissemin_xml_1_0[1][1])
        dissemin_xsd_1_0.assertValid(dissemin_xml_1_0)


