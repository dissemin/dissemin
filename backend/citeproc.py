# This module is the successor of the old crossref.py which mixed some things up.
# The module will provide essentially two ways to retrieve metadata from a DOI.
# 1. single DOI with content negotiation via dx.doi.org
# 2. mass import from CrossRef, i.e. get all DOI that they have.
# The strategy in the first case will be to check wether we have the DOI in our system and if the last update is not to long ago, we just skip.
# This has the reason, that a users might wait if they refresh their profile.

import logging
import re
import requests

from datetime import date
from datetime import datetime
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from backend.doiprefixes import free_doi_prefixes
from backend.pubtype_translations import CITEPROC_PUBTYPE_TRANSLATION
from backend.utils import request_retry
from backend.utils import utf8_truncate
from papers.baremodels import BareName
from papers.baremodels import BareOaiRecord
from papers.baremodels import BarePaper
from papers.doi import doi_to_crossref_identifier
from papers.doi import doi_to_url
from papers.doi import to_doi
from papers.models import OaiSource
from papers.models import OaiRecord
from papers.models import Paper
from papers.name import normalize_name_words
from papers.name import parse_comma_name
from papers.utils import jpath
from papers.utils import sanitize_html
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


    @staticmethod
    def is_oa_license(license_url):
        """
        This function returns whether we expect a publication under a given license
        to be freely available from the publisher.

        Licenses are as expressed in CrossRef: see http://api.crossref.org/licenses
        """
        if "creativecommons.org/licenses/" in license_url:
            return True
        oa_licenses = set([
                "http://koreanjpathol.org/authors/access.php",
                "http://olabout.wiley.com/WileyCDA/Section/id-815641.html",
                "http://pubs.acs.org/page/policy/authorchoice_ccby_termsofuse.html",
                "http://pubs.acs.org/page/policy/authorchoice_ccbyncnd_termsofuse.html",
                "http://pubs.acs.org/page/policy/authorchoice_termsofuse.html",
                "http://www.elsevier.com/open-access/userlicense/1.0/",
                ])
        return license_url in oa_licenses


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
    def _convert_to_name_pair(dct):
        """ Converts a dictionary {'family':'Last','given':'First'} to ('First','Last') """
        result = None
        if 'family' in dct and 'given' in dct:
            result = (dct['given'], dct['family'])
        elif 'family' in dct:  # The 'Arvind' case
            result = ('', dct['family'])
        elif 'literal' in dct:
            result = parse_comma_name(dct['literal'])
        if result:
            result = (normalize_name_words(
                result[0]), normalize_name_words(result[1]))
        return result


    @staticmethod
    def _get_abstract(data):
        """
        Tries to get the abstract an sanitize it
        """
        abstract = data.get('abstract', '')
        abstract = sanitize_html(abstract)
        return abstract


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
        name_pairs = list(map(cls._convert_to_name_pair, authors))
        if None in name_pairs:
            raise CiteprocAuthorError('Author list compromised')
        authors = [BareName.create_bare(first, last) for first, last in name_pairs]
        if not authors:
            raise CiteprocAuthorError('No list of authors in metadata')

        return authors


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
            'description' : cls._get_abstract(data),
            'identifier' : doi_to_crossref_identifier(doi),
            'issn' : issn,
            'issue' : data.get('issue', ''),
            'journal' : journal,
            'journal_title' : journal_title,
            'pages' : data.get('page', ''),
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
        title = utf8_truncate(data.get('title', ''), 1024)
        if title == '':
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

    @classmethod
    def _is_oa_by_license(cls, licenses):
        """
        Tries to figure out by license if publication is open access
        :param data: citeproc metadata
        :returns: True if is open access, else False
        """
        found_licenses = set([(license or {}).get('URL', '') for license in licenses])
        return any(map(cls.is_oa_license, found_licenses))


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

    batch_length = 30
    emit_status_every = 10
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
        total_results = 0
        loop_runs = 0
        new_papers = 0
        while cursor:
            params['cursor'] = cursor
            r = request_retry(
                url,
                params=params,
                headers=headers,
                session=s,
            )
            if cursor == '*':
                total_results = jpath('message/total-results', r.json(), 0)
                logger.info('Fetch for day: {}, number results: {}'.format(day.isoformat(), total_results))
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
                    except ValueError as e:
                        logger.exception(e)
                        logger.info(item)
                    else:
                        new_papers += 1
            # After running ten times
            loop_runs += 1
            if loop_runs % cls.emit_status_every == 0:
                logger.info('Parsed another {} papers. {} more to go'.format(cls.rows*cls.emit_status_every, total_results-loop_runs*cls.rows))

        logger.info('For day {} have {} paper been added or updated out of {}.'.format(day.isoformat(), new_papers, total_results))


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
        try:
            data['title'] = data.get('title', [])[0]
            return super()._get_title(data)
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
                cls._fetch_day(update_date.date())
            except requests.exceptions.RequestException as e:
                logger.exception(e)
                break
            else:
                source.last_update = update_date
                source.save()
                logger.info("Updated up to {}".format(update_date))
                update_date += timedelta(days=1)

    @staticmethod
    def _filter_dois_by_comma(dois):
        """
        For a given list of DOIs this, splits all DOIs containing a ','
        :param dois: List of DOIs
        :returns: DOI list with only DOI that have no comma
        """
        dois = [doi for doi in dois if ',' not in doi]
        return dois

    @classmethod
    def fetch_batch(cls, dois):
        """
        Given a list of DOIs, return for each DOI a paper
        :params dois: List of DOIS
        :returns: list with Paper (or None) and DOI as key. Note that the key is lowered!
        """
        # CrossRef allows only certain characters in doi, we just remove them to get better matching
        dois = list(map(cls.remove_unapproved_characters, dois))
        # We create a dict and populate with `None`s and then override with paper objects
        papers = dict()
        for doi in dois:
            papers[doi.lower()] = None
        # We filter DOIs with comma, we do not batch them, but return them as `None`
        dois_to_fetch = cls._filter_dois_by_comma(dois)

        headers = {
            'User-Agent' : settings.CROSSREF_USER_AGENT
        }
        url = 'https://api.crossref.org/works'
        s = requests.Session()

        while len(dois_to_fetch):
            dois_batch = dois_to_fetch[:cls.batch_length]
            dois_to_fetch = dois_to_fetch[cls.batch_length:]
            params = {
                'filter' : ','.join(['doi:{}'.format(doi) for doi in dois_batch]),
                'mailto' : settings.CROSSREF_MAILTO,
                'rows' : cls.batch_length,
            }
            try:
                r = request_retry(
                    url,
                    params=params,
                    headers=headers,
                    session=s,
                    retries=0, # There is probably a user waiting
                )
            except requests.exceptions.RequestException as e:
                # We skip the DOIs since we could not reach
                logger.info(e)
                continue
            items = jpath('message/items', r.json(), [])
            for item in items:
                try:
                    p = cls.to_paper(item)
                except CiteprocError:
                    logger.debug(item)
                else:
                    papers[p.get_doi()] = p

        p = [papers.get(doi.lower(), None) for doi in dois]

        return p


    @staticmethod
    def remove_unapproved_characters(doi):
        """
        CrossRef does allow only certain characters in a DOI: https://support.crossref.org/hc/en-us/articles/214669823-Constructing-your-identifiers
        The API seems to just drop the characters not allowed - making matching of asked an returns dois difficult
        :param doi: A doi (string) "a-z", "A-Z", "0-9" and "-._;()/"
        :returns: A doi containing only
        """
        valid_characters = r'[^a-zA-Z0-9-\._;\(\)/]'
        return re.sub(valid_characters, '', doi)


class DOIResolver(Citeproc):
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
                last_update__gte=timezone.now() - settings.DOI_OUTDATED_DURATION
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
