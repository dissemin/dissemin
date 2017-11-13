# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import gzip
from django.db import DataError

from papers.models import Paper
from papers.models import OaiSource
from papers.baremodels import BareOaiRecord
from papers.doi import doi_to_crossref_identifier
from papers.doi import doi_to_url

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

    def load_dump(self, filename):
        """
        Reads a dump from the disk and loads it to the db
        """
        with gzip.open(filename, 'r') as f:
            headers = []
            for line in f:
                from time import sleep
                fields = line.decode('utf-8').strip().split(',')
                if not headers:
                    headers = fields
                    continue
                if len(fields) != len(headers):
                    continue
                self.create_oairecord(dict(zip(headers,fields)))

    def create_oairecord(self, record):
        """
        Given one line of the dump (represented as a dict),
        add it to the corresponding paper (if it exists)
        """
        doi = record['doi']
        paper = Paper.get_by_doi(doi)
        if not paper:
            print('no such paper for doi {doi}'.format(doi))
            return

        url = record['url']
        identifier='oadoi:'+url
        source = self.oadoi_source

        if record['host_type'] == 'publisher':
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
            pdf_url=record['url'])
        try:
            paper.add_oairecord(record)
            paper.update_availability()
            paper.update_index()
        except (DataError, ValueError):
            print('Record does not fit in the DB')
