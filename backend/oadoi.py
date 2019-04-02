# -*- encoding: utf-8 -*-


import gzip
import json
import logging
from django.db import DataError

from papers.models import Paper
from papers.models import OaiSource
from papers.baremodels import BareOaiRecord
from papers.doi import doi_to_crossref_identifier
from papers.doi import doi_to_url
from papers.doi import to_doi
from backend.doiprefixes import free_doi_prefixes
from papers.errors import MetadataSourceException
from backend.utils import report_speed

logger = logging.getLogger('dissemin.' + __name__)

class OadoiAPI(object):
    """
    An interface to import an OAdoi dump into dissemin
    """
    def __init__(self):
        self.oadoi_source, _ = OaiSource.objects.get_or_create(
            identifier='oadoi_repo',
            defaults=
            {'name':'OAdoi',
            'oa':True,
            'priority':-10,
            'default_pubtype':'preprint'})

        self.crossref_source = OaiSource.objects.get(identifier='crossref')

    @report_speed(name='oadoi importing speed')
    def read_dump(self, filename, start_doi=None):
        """
        Enumerates the JSON objects in the dump, optionally starting from the given DOI
        """
        with gzip.open(filename, 'r') as f:
            start_doi_seen = start_doi is None
            for line in f:
                record = json.loads(line.decode('utf-8'))
                if not start_doi_seen and record.get('doi') == start_doi:
                    start_doi_seen = True
                if start_doi_seen:
                    yield record


    def load_dump(self, filename, start_doi=None, update_index=False, create_missing_dois=True):
        """
        Reads a dump from the disk and loads it to the database.
        """
        for record in self.read_dump(filename, start_doi=start_doi):
            self.create_oairecord(record, update_index, create_missing_dois)

    def create_oairecord(self, record, update_index=True, create_missing_dois=True):
        """
        Given one line of the dump (represented as a dict),
        add it to the corresponding paper (if it exists)
        """
        doi = to_doi(record['doi'])
        if not doi:
            return
        prefix = doi.split('/')[0]
        if prefix in free_doi_prefixes:
            return
        if not record.get('oa_locations'):
            return

        paper = Paper.get_by_doi(doi)
        if not paper:
            if not create_missing_dois:
                return
            try:
                paper = Paper.create_by_doi(doi)
            except (MetadataSourceException, ValueError):
                return
            if not paper:
                logger.info('no such paper for doi {doi}'.format(doi=doi))
                return
        logger.info(doi)
        paper.cache_oairecords()

        for oa_location in record.get('oa_locations') or []:
            url = oa_location['url']

            # just to speed things up a bit...
            if paper.pdf_url == url:
                return

            identifier='oadoi:'+url
            source = self.oadoi_source

            if oa_location['host_type'] == 'publisher':
                url = doi_to_url(doi)
                identifier = doi_to_crossref_identifier(doi)
                source = self.crossref_source

            record = BareOaiRecord(
                paper=paper,
                doi=doi,
                pubtype=paper.doctype,
                source=source,
                identifier=identifier,
                splash_url=url,
                pdf_url=oa_location['url'])
            try:
                # We disable checks by DOI since we know the paper has been looked up by DOI already.
                old_pdf_url = paper.pdf_url
                paper.add_oairecord(record, check_by_doi=False)
                super(Paper, paper).update_availability()
                if old_pdf_url != paper.pdf_url:
                    paper.save()
                    if update_index:
                        paper.update_index()
            except (DataError, ValueError):
                logger.warning('Record does not fit in the DB')
