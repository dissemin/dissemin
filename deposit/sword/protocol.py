import requests
import logging

from io import BytesIO
from lxml import etree
from zipfile import ZipFile

from django.utils.translation import ugettext as _

from deposit.protocol import DepositError
from deposit.protocol import RepositoryProtocol

logger = logging.getLogger('dissemin.' + __name__)
        
        
# Namespaces
METS_NAMESPACE = "http://www.loc.gov/METS/"
MODS_NAMESPACE = "http://www.loc.gov/mods/v3"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"

METS = "{%s}" % METS_NAMESPACE
MODS = "{%s}" % MODS_NAMESPACE
XLINK = "{%s}" % XLINK_NAMESPACE


class SWORDMETSProtocol(RepositoryProtocol):
    """
    A protocol that performs a deposito via SWORDv2 using a METS Container.
    """

    def __str__(self):
        """
        Return human readable class name
        """
        return "SWORD Protocol (METS)"

    
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
            * MDTYPE in dmdSec/mdWrap is always `OTHER`
            * One and only file that is named `document.pdf`

        :params metadata: Bibliographic metadata as lxml etree
        :returns: complete mets as string
        """

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


class SWORDMETSMODSProtocol(SWORDMETSProtocol):
    """
    Protocol that implements MODS metadata with SWORDMETSProtocol
    """

    def __str__(self):
        """
        Return human readable class name
        """
        return "SWORD Protocol (MODS)"


    def _get_xml_metadata(self, form):
        """
        Creates metadata as lxml etree in MODS
        """
        self.log("### Creating MODS metadata from publication and form")

        # Fetch the first OaiRecord with highest OaiSource priority and journal as well as publisher
        publication = self.paper.oairecord_set.filter(
            journal_title__isnull=False,
            publisher_name__isnull=False
        ).order_by('priority').first()

        # If this is not available, take the first one
        if publication is None:
           publication = self.paper.oairecord_set.order_by('priority').first()

        NSMAP = {
            None: MODS_NAMESPACE,
        }

        # Creation of root
        mods_xml = etree.Element(MODS + 'mods', nsmap=NSMAP)
        mods_xml.set('version', '3.7')

        # Abstract
        mods_abstract = etree.SubElement(mods_xml, MODS + 'abstract')
        mods_abstract.text = form.cleaned_data['abstract']

        # Date
        mods_origin_info = etree.SubElement(mods_xml, MODS + 'originInfo')
        mods_date_issued = etree.SubElement(mods_origin_info, MODS + 'dateIssued')
        mods_date_issued.set('encoding', 'w3cdtf')
        mods_date_issued.text = str(self.paper.pubdate)

        # Identifier / DOI and relatedItem
        if publication:
            # DOI
            if publication.doi:
                mods_doi = etree.SubElement(mods_xml, MODS + 'identifier')
                mods_doi.set('type', 'doi')
                mods_doi.text = publication.doi

            # Publisher
            publisher = publication.publisher
            if publication.publisher is not None:
                publisher = publication.publisher.name
            else:
                publisher = publication.publisher_name

            if publisher is not None:
                mods_publisher = etree.SubElement(mods_origin_info, MODS + 'publisher')
                mods_publisher.text = publisher

            # relatedItem
            related_item = self._get_xml_metadata_relatedItem(publication)
            if related_item is not None:
                mods_xml.insert(0, related_item)

        # Language
        # TODO Fixture + Routine

        # DDC
        # TODO Fixture + Routine

        # Name / Authors list
        for author in self.paper.authors:
            mods_name = etree.SubElement(mods_xml, MODS + 'name')
            mods_name.set('type', 'personal')
            mods_last_name = etree.SubElement(mods_name, MODS + 'namePart')
            mods_last_name.set('type', 'family')
            mods_last_name.text = author.name.last
            mods_first_name = etree.SubElement(mods_name, MODS + 'namePart')
            mods_first_name.set('type', 'given')
            mods_first_name.text = author.name.first

        # Title
        mods_title_info = etree.SubElement(mods_xml, MODS + 'titleInfo')
        mods_title = etree.SubElement(mods_title_info, MODS + 'title')
        mods_title.text = self.paper.title

        # Document type
        mods_type = etree.SubElement(mods_xml, MODS + 'genre')
        mods_type.text = self.paper.doctype

        return mods_xml

        
    def _get_xml_metadata_relatedItem(self, publication):
        """
        Creates the mods item ``relatedItem`` if available
        :param publication: A OaiRecord corresponding to the paper
        :returns: lxml object or ``None``
        """
        related_item = None
        related_item_data = dict()

        # We set the title and publisher, but prefer values from Journal or Publisher object if available
        journal = publication.journal
        issn = None
        eissn = None
        if publication.journal is not None:
            journal = publication.journal.title
            issn = publication.journal.issn
            eissn = publication.journal.essn
        else:
            journal = publication.journal_title

        # Set the title
        if journal is not None:
            related_item_title_info = etree.Element(MODS + 'titleInfo')
            related_item_title = etree.SubElement(related_item_title_info, MODS + 'title')
            related_item_title.text = journal
            related_item_data['title'] = related_item_title_info

        # Set issn
        if issn is not None:
            related_item_issn = etree.Element(MODS + 'identifier')
            related_item_issn.set('type', 'issn')
            related_item_issn.text = issn
            related_item_data['issn'] = related_item_issn

        # Set issn
        if eissn is not None:
            related_item_eissn = etree.Element(MODS + 'identifier')
            related_item_eissn.set('type', 'eissn')
            related_item_eissn.text = eissn
            related_item_data['eissn'] = related_item_eissn

        # relatedItem - part
        part = dict()

        # Set pages
        if publication.pages is not None:
            pages = publication.pages.split('-', 1)
            related_item_pages = etree.Element(MODS + 'extent')
            related_item_pages.set('unit', 'pages')
            if len(pages) == 1:
                related_item_pages_total = etree.SubElement(related_item_pages, MODS + 'total')
                related_item_pages_total.text = publication.pages
                part['pages'] = related_item_pages
            else:
                start = pages[0]
                end = pages[1]
                related_item_pages_start = etree.SubElement(related_item_pages, MODS + 'start')
                related_item_pages_start.text = start
                related_item_pages_start = etree.SubElement(related_item_pages, MODS + 'end')
                related_item_pages_start.text = end
                part['pages'] = related_item_pages

        # Set issue
        if publication.issue is not None:
            related_item_issue = etree.Element(MODS + 'detail')
            related_item_issue.set('type', 'issue')
            related_item_issue_number = etree.SubElement(related_item_issue, MODS + 'number')
            related_item_issue_number.text = publication.issue
            part['issue'] = related_item_issue

        # Set volume
        if publication.volume is not None:
            related_item_volume = etree.Element(MODS + 'detail')
            related_item_volume.set('type', 'volume')
            related_item_volume_number = etree.SubElement(related_item_volume, MODS + 'number')
            related_item_volume_number.text = publication.volume
            part['volume'] = related_item_volume

        # Make parts if existing
        if len(part) >= 1:
            related_item_part = etree.Element(MODS + 'part')
            for item in part.values():
                related_item_part.insert(0, item)
            related_item_data['part'] = related_item_part

        # Make relatedItem if existing
        if len(related_item_data) >= 1:
            related_item = etree.Element(MODS + 'relatedItem')
            for item in related_item_data.values():
                related_item.insert(0, item)
        
        return related_item

