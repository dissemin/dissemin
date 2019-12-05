# This module is the successor of the old crossref.py which mixed some things up.
# The module will provide essentially two ways to retrieve metadata from a DOI.
# 1. single DOI with content negotiation via dx.doi.org
# 2. mass import from CrossRef, i.e. get all DOI that they have.
# The strategy in the first case will be to check wether we have the DOI in our system and if the last update is not to long ago, we just skip.
# This has the reason, that a users might wait if they refresh their profile.

import logging
import requests

from datetime import date
from datetime import datetime
from datetime import timedelta

from django.conf import settings

from backend.crossref import convert_to_name_pair
from backend.crossref import is_oa_license
from backend.doiprefixes import free_doi_prefixes
from backend.pubtype_translations import CITEPROC_PUBTYPE_TRANSLATION
from backend.utils import request_retry
from papers.baremodels import BareName
from papers.baremodels import BareOaiRecord
from papers.baremodels import BarePaper
from papers.doi import doi_to_crossref_identifier
from papers.doi import doi_to_url
from papers.doi import to_doi
from papers.models import OaiSource
from papers.models import OaiRecord
from papers.models import Paper
from papers.utils import jpath
from papers.utils import tolerant_datestamp_to_datetime
from papers.utils import validate_orcid
from papers.utils import valid_publication_date
from publishers.models import AliasPublisher
from publishers.models import Journal
from publishers.models import Publisher


logger = logging.getLogger('dissemin.' + __name__)


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

class CiteprocPubtypeError(CiteprocError):
    pass

class CiteprocTitleError(CiteprocError):
    pass


class Citeproc():
    """
    This class is a citeproc parser.
    """

    @classmethod
    def to_paper(cls, data):
        """
        Call this function to convert citeproc metadata into a paper object
        Our strategy is as follows:
        We collect first all data necessary, if me miss something, then we raise CiteprocError.
        If we have collected everything, we pass that to the corresponding baremodels.
        :param data: citeproc metadata. Note that CrossRef does put its citeproc into a message block
        :returns: Paper object
        :raises: CiteprocError
        """
        if not isinstance(data, dict):
            raise CiteprocError('Invalid metadaformat, expecting dict')
        bare_paper_data = cls._get_paper_data(data)
        bare_oairecord_data = cls._get_oairecord_data(data)

        bare_paper = BarePaper.create(**bare_paper_data)
        bare_oairecord = BareOaiRecord(paper=bare_paper, **bare_oairecord_data)
        bare_paper.add_oairecord(bare_oairecord)
        bare_paper.update_availability()

        paper = Paper.from_bare(bare_paper)
        paper.update_index()
        return paper




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


    @staticmethod
    def _get_issn(data):
        """
        :param data: citeproc metadata
        :returns: ISSN or ''
        """
        issn = data.get('ISSN', '')
        if isinstance(issn, list):
            try:
                issn = issn[0]
            except IndexError:
                issn = ''
        return issn


    @classmethod
    def _get_oairecord_data(cls, data):
        """
        :param data: citeproc metadata
        :returns: Returns a dict, ready to passed to a BarePaper instance
        :raises: CiteprocError
        """
        doi = cls._get_doi(data)
        splash_url = doi_to_url(doi)
        licenses = data.get('licenses', [])
        pdf_url = cls._get_pdf_url(doi, licenses, splash_url)

        journal_title = cls._get_container(data)
        issn = cls._get_issn(data)
        journal = Journal.find(issn=issn, title=journal_title)

        publisher_name = data.get('publisher', '')[:512]
        publisher = cls._get_publisher(publisher_name, journal)

        bare_oairecord_data = {
            'doi' : doi,
            'identifier' : doi_to_crossref_identifier(doi),
            'issn' : issn,
            'issue' : data.get('issue', ''),
            'journal' : journal,
            'journal_title' : journal_title,
            'pages' : data.get('pages', ''),
            'pdf_url' : pdf_url,
            'pubdate' : cls._get_pubdate(data),
            'publisher' : publisher,
            'publisher_name' : publisher_name,
            'pubtype' : cls._get_pubtype(data),
            'source' : OaiSource.objects.get(identifier='crossref'),
            'splash_url' : splash_url,
            'volume' : data.get('volume', ''),
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
            'author_names' : cls._get_authors(data),
            'orcids' : cls._get_orcids(data),
            'pubdate' : cls._get_pubdate(data),
            'title' : cls._get_title(data),
        }
        
        return bare_paper_data


    @classmethod
    def _get_pdf_url(cls, doi, licenses, url):
        """
        Tries to fgiure out, if the publication is OA by inspecting metadata, if so, sets url
        """
        if cls._is_oa_by_doi(doi) or cls._is_oa_by_license(licenses):
            return url
        else:
            return ''


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


    @staticmethod
    def _get_publisher(name, journal):
        """
        Tries to find a publisher PK, based on journal or name
        :param name: Name of the publisher
        :param journal: Journal object
        """
        if journal is not None:
            publisher = journal.publisher
            AliasPublisher.increment(name, publisher)
        else:
            publisher = Publisher.find(name)
        return publisher


    @staticmethod
    def _get_pubtype(data):
        """
        Returns the pub type
        """
        p = data.get('type')
        if p is None:
            raise CiteprocPubtypeError('No publication type in metadata')
        # We do some logging on pubtypes that occur
        try:
            pubtype = CITEPROC_PUBTYPE_TRANSLATION[p]
        except KeyError:
            logger.error('Unknown pubtype: {} - This is data: {}'.format(p, data))
            pubtype = 'other'
        return pubtype


    @classmethod
    def _get_title(cls, data):
        """
        :param: citeproc metadata
        :returns: title
        :raises: CiteprocError
        """
        # Check for a title
        title = data.get('title', '')[:1024]
        if title is '':
            raise CiteprocTitleError('No title in metadata')
        return title


    @staticmethod
    def _is_oa_by_doi(doi):
        """
        Tries to figure by doi if publication is open access
        :param data: citeproc metadata
        :returns: True if is open access, else False
        """
        doi_prefix = doi.split('/')[0]
        return doi_prefix in free_doi_prefixes

    @staticmethod
    def _is_oa_by_license(licenses):
        """
        Tries to figure out by license if publication is open access
        :param data: citeproc metadata
        :returns: True if is open access, else False
        """
        found_licenses = set([(license or {}).get('URL', '') for license in licenses])
        return any(map(is_oa_license, found_licenses))


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
            d = cls._parse_date_parts(data.get('date-parts')[0])
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

    rows = 500

    @classmethod
    def _fetch_day(cls, day):
        """
        Fetches a whole day from CrossRef
        """
        filters = {
            'from-update-date' : day.isoformat(),
            'until-update-date' : day.isoformat(),
        }
        params = {
                'filter' : ','.join('{}:{}'.format(key, value) for key, value in filters.items()),
                'rows' : cls.rows,
                'mailto' : settings.CROSSREF_MAILTO,
        }
        url = 'https://api.crossref.org/works'
        headers = {
            'User-Agent':  settings.CROSSREF_USER_AGENT,
        }

        s = requests.Session()
        cursor = '*'
        while cursor:
            params['cursor'] = cursor
            r = request_retry(
                url,
                params=params,
                headers=headers,
                session=s,
            )
            cursor = jpath('message/next-cursor', r.json())
            items = jpath('message/items', r.json(), [])
            if len(items) == 0:
                cursor = False
            else:
                for item in items:
                    try:
                        cls.to_paper(item)
                    except CiteprocError:
                        logger.debug(item)


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
        title = data.get('title', [])
        try:
            return title[0][:1024]
        except IndexError:
            raise CiteprocTitleError('No title in metadata')


    @classmethod
    def fetch_latest_records(cls):
        """
        Fetches the latest records from CrossRef API
        """
        source = OaiSource.objects.get(identifier='crossref')
        update_date = source.last_update + timedelta(days=1)
        today = date.today()
        while update_date.date() < today:
            try:
                cls._fetch_day(update_date)
            except requests.exceptions.RequestException as e:
                logger.exception(e)
                break
            else:
                source.last_update = update_date
                source.save()
                logger.info("Updated up to {}".format(update_date))
                update_date += timedelta(days=1)


class DOI(Citeproc):
    """
    This class fetches citeproc metadata with content negotiation via DOI resolver.
    The main strategy here is to accelerate the ingest by checking if we already have an OaiRecord and update it only if the entry is rather old
    """

    headers = {
        'Accept' : 'application/citeproc+json',
    }
    timeout = 0.500 # half a second as timeout, the might user waiting


    @staticmethod
    def _is_up_to_date(doi):
        """
        Checks if doi is already in the database and wheter it is up to date
        :param doi: DOI to check
        :returns: True/False
        """
        try:
            return OaiRecord.objects.select_related('about').get(
                doi=doi,
                source__identifier='crossref',
                last_update__gte=date.today() - settings.DOI_OUTDATED_DURATION
            )
        except OaiRecord.DoesNotExist:
            return None


    @classmethod
    def save_doi(cls, doi):
        """
        Fetches a single DOI and updates if necessary
        :param doi: A (valid) DOI
        :returns: Paper object
        :raises: CiteprocError or RequestException
        """
        record = cls._is_up_to_date(doi)
        if record is not None:
            return record.about

        url = '{}{}'.format(settings.DOI_RESOLVER_ENDPOINT, doi)
        r = requests.get(
            url=url,
            headers=cls.headers,
            timeout=cls.timeout,
        )

        r.raise_for_status()

        p = cls.to_paper(r.json())

        return p
