# -*- encoding: utf-8 -*-


import gzip
import json
from django.db import DataError

from papers.models import Paper
from papers.models import OaiSource
from papers.baremodels import BareOaiRecord
from papers.doi import doi_to_crossref_identifier
from papers.doi import doi_to_url
from papers.doi import to_doi
from backend.doiprefixes import free_doi_prefixes
from papers.errors import MetadataSourceException

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

    def load_dump(self, filename, start_doi=None, update_index=False, create_missing_dois=True):
        """
        Reads a dump from the disk and loads it to the db
        """
        with gzip.open(filename, 'r') as f:
            start_doi_seen = start_doi is None
            for idx, line in enumerate(f):
                record = json.loads(line.decode('utf-8'))
                if not start_doi_seen and record.get('doi') == start_doi:
                    start_doi_seen = True
                if idx % 10000 == 0:
                    print(idx, record.get('doi'))

                if start_doi_seen:
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

        paper = Paper.get_by_doi(doi)
        if not paper:
            if not create_missing_dois:
                return
            try:
                paper = Paper.create_by_doi(doi)
            except (MetadataSourceException, ValueError):
                return
            if not paper:
                print('no such paper for doi {doi}'.format(doi=doi))
                return

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
                paper.add_oairecord(record)
                paper.update_availability()
                if update_index:
                    paper.update_index()
            except (DataError, ValueError):
                print('Record does not fit in the DB')
