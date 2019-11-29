# This module is the successor of the old crossref.py which mixed some things up.
# The module will provide essentially two ways to retrieve metadata from a DOI.
# 1. single DOI with content negotiation via dx.doi.org
# 2. mass import from CrossRef, i.e. get all DOI that they have.
# The strategy in the first case will be to check wether we have the DOI in our system and if the last update is not to long ago, we just skip.
# This has the reason, that a users might wait if they refresh their profile.

from datetime import datetime

from backend.crossref import convert_to_name_pair
from papers.baremodels import BareName
from papers.doi import to_doi
from papers.utils import tolerant_datestamp_to_datetime
from papers.utils import validate_orcid
from papers.utils import valid_publication_date


class CiteprocError(Exception):
    pass

class CiteprocAuthorError(CiteprocError):
    pass

class CiteprocContainerTitleError(CiteprocError):
    pass

class CiteprocDateError(CiteprocError):
    pass

class CiteprocDOIError(CiteprocError):
    pass

class CiteprocTitleError(CiteprocError):
    pass


class Citeproc():
    """
    This class is a citeproc parser.
    """

    @staticmethod
    def to_paper(data):
        """
        Call this function to convert citeproc metadata into a paper object
        Our strategy is as follows:
        We collect first all data necessary, if me miss something, then we raise CiteprocError.
        If we have collected everything, we pass that to the corresponding baremodels.
        :param data: citeproc metadata. Note that CrossRef does put its citeproc into a message block
        :returns: Paper object or None if no paper was created
        :raises: CiteprocError
        """
        if not isinstance(data, dict):
            raise CiteprocError('Invalid metadaformat, expecting dict')


    @staticmethod
    def _get_affiliation(author_elem):
        """
        Affiliations come as a list of dict.
        We return the first affiliation if any
        :param author_elem: citeproc author element
        :returns: affiliation name or None
        """
        for dct in author_elem.get('affiliation', []):
            if 'name' in dct:
                return dct['name']


    @classmethod
    def _get_affiliations(cls, data):
        """
        :param data: citeproc data
        :returns: list of affiliations, of length author
        :raises: CiteprocAuthorError
        """
        authors = data.get('author')
        if not isinstance(authors, list):
            raise CiteprocAuthorError('No list of authors in metadata')
        return list(map(cls._get_affiliation, authors))


    @classmethod
    def _get_authors(cls, data):
        """
        :param data: citeproc metadata
        :returns: List of barenames
        :raises: CiteprocAuthorError
        """
        authors = data.get('author')
        if not isinstance(authors, list):
            raise CiteprocAuthorError('No list of authors in metadata')
        name_pairs = list(map(convert_to_name_pair, authors))
        if None in name_pairs:
            raise CiteprocAuthorError('Author list compromised')
        return [BareName.create_bare(first, last) for first, last in name_pairs]


    @staticmethod
    def _get_container(data):
        """
        :param data: citeproc metadata
        :returns: Container title
        :raises: CiteprocContainerTitleError
        """
        container = data.get('container-title')
        if not container:
            raise CiteprocContainerTitleError('No container-title in metadata')
        return container[:512]


    @staticmethod
    def _get_doi(data):
        """
        :param data: citeproc metadata
        :returns: doi or None
        """
        doi = to_doi(data.get('DOI', ''))
        if doi is None:
            raise CiteprocDOIError('Invalid DOI in metadata')
        return doi


    @classmethod
    def _get_oairecord_data(cls, data):
        """
        :param data: citeproc metadata
        :returns: Returns a dict, ready to passed to a BarePaper instance
        :raises: CiteprocError
        """
        doi = cls._get_doi(data)
        bare_oairecord_data = {
            'doi' : doi,
            'journal_title' : cls._get_container(data),
            'pubdate' : cls._get_pubdate(data),
        }

        return bare_oairecord_data


    @staticmethod
    def _get_orcid(author_elem):
        """
        Return a validated orcid or None
        :param author_elem: author as in citeproc
        :returns: orcid or None
        """
        return validate_orcid(author_elem.get('ORCID'))


    @classmethod
    def _get_orcids(cls, data):
        """
        :param data: citeproc metadata
        :returns: list of orcids, of length author
        :raises: CiteprocAuthorError
        """
        authors = data.get('author')
        if not isinstance(authors, list):
            raise CiteprocAuthorError('No list of authors in metadata')
        return list(map(cls._get_orcid, authors))


    @classmethod
    def _get_paper_data(cls, data):
        """
        :param data: citeproc metadata
        :returns: Returns a dict, ready to passed to a BarePaper instance
        :raises: CiteprocError
        """
        bare_paper_data = {
            'affiliations' : cls._get_affiliations(data),
            'authors' : cls._get_authors(data),
            'orcids' : cls._get_orcids(data),
            'pubdate' : cls._get_pubdate(data),
            'title' : cls._get_title(data),
        }
        
        return bare_paper_data


    @classmethod
    def _get_pubdate(cls, data):
        """
        Get the publication date out of a record. If 'issued' is not present
        we default to 'deposited' although this might be quite inaccurate.
        But this case is rare anyway.
        """
        pubdate = None
        if 'issued' in data:
            pubdate = cls._parse_date(data['issued'])
        if pubdate is None and 'created' in data:
            pubdate = cls._parse_date(data['created'])
        if pubdate is None and 'deposited' in data:
            pubdate = cls._parse_date(data['deposited'])
        if pubdate is None:
            raise CiteprocDateError('No valid date found in metadata')
        return pubdate


    @classmethod
    def _get_title(cls, data):
        """
        :param: citeproc metadata
        :returns: title
        :raises: CiteprocError
        """
        # Check for a title
        title = data.get('title')
        if title is None:
            raise CiteprocTitleError('No title in metadata')
        return title


    @classmethod
    def _parse_date(cls, data):
        """
        Parse the date representation from citeproc to a date object
        :param data: date extracted from citeproc
        :returns: date object or None
        """
        if not isinstance(data, dict):
            return None
        d = None
        # First we try with date parts
        try:
            d = cls._parse_date_parts(data.get('date-parts'))
        except Exception:
            pass

        # If this has no success, we try with raw date
        if d is None and data.get('raw') is not None:
            d = tolerant_datestamp_to_datetime(data['raw']).date()

        # We validate, if bad, then set to None
        if not valid_publication_date(d):
            d = None

        return d

    @classmethod
    def _parse_date_parts(cls, date_parts):
        """
        :param date_parts: date-parts as in citeproc, i.e. a list of integers
        :returns: date object
        :raises: Exception if something went wrong
        """
        d = "-".join([
            str(date_parts[0]),
            str(date_parts[1]).zfill(2) if len(date_parts) >= 2 else "01",
            str(date_parts[2]).zfill(2) if len(date_parts) >= 3 else "01",
        ])
        return datetime.strptime(d, "%Y-%m-%d").date()
        
        
class CrossRef(Citeproc):
    """
    This class can parse CrossRef metadata, which is similar to citeproc and has functionality to fetch from CrossRef API
    """

    @staticmethod
    def _get_container(data):
        container_title = data.get('container-title')
        if not isinstance(container_title, list):
            raise CiteprocContainerTitleError('container-title in metadata invalid')
        return container_title[0][:512]


    @classmethod
    def _get_title(cls, data):
        """
        The title in CrossRef citeproc is in a list
        :param: citeproc metadata
        :returns: title
        :raises: CiteprocError
        """
        title = super()._get_title(data)
        try:
            return title[0]
        except IndexError:
            raise CiteprocTitleError('No title in metadata')
