from lxml import etree

from deposit.protocol import RepositoryProtocol

class SWORDMETSProtocol(RepositoryProtocol):
    """
    A protocol that performs a deposito via SWORDv2 using a METS Container.
    """
    def __repr__(self):
        """
        Return the class name
        """
        return self.__name__

    def __str__(self):
        """
        Return human readable class name
        """
        return "SOWRD Protocol (METS)"

    @staticmethod
    def _get_mets(metadata):
        """
        Creates a mets xml from metadata
        Policy for creation is: One-time-usage, so keep the document as small as possible. This means
            * Attributes and elements are omitted if not needed
            * There is one and only one dmdSec
            * MDTYPE in dmdSec/mdWrap is always ``OTHER``
            * One and only file that is named ``document.pdf``
        
        :params metadata: Bibliographic metadata as lxml etree
        :returns: complete mets as string
        """
        METS_NAMESPACE = "http://www.loc.gov/METS/"
        XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
        XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"

        METS = "{%s}" % METS_NAMESPACE
        XLINK = "{%s}" % XLINK_NAMESPACE

        NSMAP = {
            None : METS_NAMESPACE,
            'xlink' : XLINK_NAMESPACE,
            'xsi' : XSI_NAMESPACE
        }

        # Creation of document root and dmdSec
        mets_xml = etree.Element(METS + 'mets', nsmap=NSMAP)
        mets_dmdSec = etree.SubElement(mets_xml, METS + 'dmdSec', ID='d_dmd_1')
        mets_mdWrap = etree.SubElement(mets_dmdSec, METS + 'mdWrap', MDTYPE='OTHER')
        mets_xmlData = etree.SubElement(mets_mdWrap, METS + 'xmlData')
        mets_xmlData.insert(0, metadata)

        # Creation of fileSec
        mets_fileSec = etree.SubElement(mets_xml, METS + 'fileSec')
        mets_fileGrp = etree.SubElement(mets_fileSec, METS + 'fileGrp')
        mets_file = etree.SubElement(mets_fileGrp, METS + 'file', ID='d_file_1')
        mets_FLocat = etree.SubElement(mets_file, METS + 'FLocat')
        mets_FLocat.set(XLINK + 'href', 'document.pdf')
        mets_FLocat.set('LOCTYPE', 'URL')

        # Creation of structMap
        mets_structMap = etree.SubElement(mets_xml, METS + 'structMap')
        mets_div_dmd = etree.SubElement(mets_structMap, METS + 'div', DMDID='d_dmd_1')
        mets_div_file = etree.SubElement(mets_div_dmd, METS + 'div')
        etree.SubElement(mets_div_file, METS + 'fptr', FILEID='d_file_1')

        return etree.tostring(mets_xml, pretty_print=True, encoding='utf-8', xml_declaration=True).decode()

    def _get_mets_container(self, pdf, mets):
        """
        Creates a mets package, i.e. zip for a given file and given schema. The filename in the package is taken from mets.

        :params pdf: A pdf file
        :params mets: A mets as lxml etree
        :returns: a zip object
        """
        pass

    def submit_deposit(self, pdf, form, metadata):
        """
        Submit paper to the repository. This is a wrapper for the subclasses. It creates the METS container and deposits.

        :param pdf: Filename to dhe PDF file to submit
        :param form: The form returned by get_form and completed by the user
        :param metadata: Metadata formated as lxml etree, ready to be inserted into METS

        :returns: DepositResult object
        """
        pass
    




