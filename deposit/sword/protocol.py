import requests
import logging

from io import BytesIO
from lxml import etree
from zipfile import ZipFile

from django.utils.translation import ugettext as _

from deposit.protocol import DepositError
from deposit.protocol import RepositoryProtocol

logger = logging.getLogger('dissemin.' + __name__)


class SWORDMETSProtocol(RepositoryProtocol):
    """
    A protocol that performs a deposito via SWORDv2 using a METS Container.
    """

    def __str__(self):
        """
        Return human readable class name
        """
        return "SOWRD Protocol (METS)"

    
    @staticmethod
    def _get_deposit_result(response):
        """
        This function returns a Deposit Result in case of a successful deposition. Please override this function in your sub-protocol.
        """
        raise NotImplementedError("Function not implemented")
    

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


    @staticmethod
    def _get_mets_container(pdf, mets):
        """
        Creates a mets package, i.e. zip for a given file and given schema. The filename in the package is taken from mets.

        :params pdf: A pdf file
        :params mets: A mets as lxml etree
        :returns: a zip object
        """
        s = BytesIO()
        with ZipFile(s, 'w') as zip_file:
            zip_file.write(pdf, 'document.pdf')
            zip_file.writestr('mets.xml', mets)
        return s


    @staticmethod
    def _get_xml_metadata(form):
        """
        This function returns metadata as lxml etree object, that is ready to inserted into a mets.xml. Override this function in your subclassed protocol.
        """
        raise NotImplementedError("Function not implemented")


    def submit_deposit(self, pdf, form):
        """
        Submit paper to the repository. This is a wrapper for the subclasses and calls some protocol specific functions. It creates the METS container and deposits.

        :param pdf: Filename to dhe PDF file to submit
        :param form: The form returned by get_form and completed by the user

        :returns: DepositResult object
        """

        # Raise error if login credentials are missing. These are not mandatory in Admin UI, since alternatively an API Key can be used, but not for SWORD
        if not (self.repository.username and self.repository.password):
            raise DepositError(_("Username or password not provided for this repository. Please contact the Dissemin team."))

        metadata = self._get_xml_metadata(form)
        mets = self._get_mets(metadata)

        zipfile = self._get_mets_container(pdf, mets)

        # Send request to repository
        self.log("### Preparing request to repository")

        auth = (self.repository.username, self.repository.password)
        files = {'file': ('mets.zip', zipfile.getvalue(), 'application/zip')}
        headers = {'Content-type': 'application/zip'}

        self.log("### Sending request")
        r = requests.post(self.repository.endpoint, auth=auth, headers=headers, files=files, timeout=20)

        r.raise_for_status()

        self.log("### Status response: %s" % r.status_code)

        # Deposit was successful

        deposit_result = self._get_deposit_result(r.text)

        return deposit_result
