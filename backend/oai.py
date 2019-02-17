# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#



from datetime import datetime

from backend.papersource import PaperSource

from django.db import transaction
from multiprocessing_generator import ParallelGenerator
from oaipmh.client import Client

from oaipmh.error import NoRecordsMatchError
from oaipmh.metadata import MetadataRegistry
from oaipmh.metadata import oai_dc_reader
from papers.models import Paper
from backend.translators import OAIDCTranslator
from backend.translators import BASEDCTranslator
from backend.oaireader import base_dc_reader

class OaiPaperSource(PaperSource):  # TODO: this should not inherit from PaperSource
    """
    A paper source that fetches records from the OAI-PMH proxy
    (typically: proaixy).

    It uses the ListRecord verb to fetch records from the OAI-PMH
    source. Each record is then converted to a :class:`BarePaper`
    by an :class:`OaiTranslator` that handles the format
    the metadata is served in.
    """

    def __init__(self, oaisource, day_granularity=False, *args, **kwargs):
        """
        This sets up the paper source.

        :param endpoint: the address of the OAI-PMH endpoint
            to fetch from.
        :param day_granularity: should we use day-granular timestamps
            to fetch from the proxy or full timestamps (default: False,
            full timestamps)

        See the protocol reference for more information on timestamp
        granularity:
        https://www.openarchives.org/OAI/openarchivesprotocol.html
        """
        super(OaiPaperSource, self).__init__(*args, **kwargs)
        if not oaisource.endpoint:
            raise ValueError('No OAI endpoint was configured for this OAI source.')

        self.registry = MetadataRegistry()
        self.registry.registerReader('oai_dc', oai_dc_reader)
        self.registry.registerReader('base_dc', base_dc_reader)
        self.client = Client(oaisource.endpoint, self.registry)
        self.client._day_granularity = day_granularity
        self.translators = {
            'oai_dc': OAIDCTranslator(oaisource),
            'base_dc': BASEDCTranslator(oaisource),
        }

    # Translator management

    def add_translator(self, translator):
        """
        Adds the given translator to the paper source,
        so that we know how to translate papers in the given format.

        The paper source cannot hold more than one translator
        per OAI format (it decides what translator to use
        solely based on the format) so if there is already a translator
        for that format, it will be overriden.
        """
        self.translators[translator.format()] = translator

    # Record ingestion

    def ingest(self, from_date=None, metadataPrefix='oai_dc',
               resumptionToken=None):
        """
        Main method to fill Dissemin with papers!

        :param from_date: only fetch papers modified after that date in
                          the proxy (useful for incremental fetching)
        :param metadataPrefix: restrict the ingest for this metadata
                          format
        """
        args = {'metadataPrefix':metadataPrefix}
        if from_date:
            args['from_'] = from_date
        if resumptionToken:
            args['resumptionToken'] = resumptionToken
        records = self.client.listRecords(**args)
        self.process_records(records, metadataPrefix)

    def create_paper_by_identifier(self, identifier, metadataPrefix):
        """
        Queries the OAI-PMH proxy for a single paper.

        :param identifier: the OAI identifier to fetch
        :param metadataPrefix: the format to use (a translator
                    has to be registered for that format, otherwise
                    we return None with a warning message)
        :returns: a Paper or None
        """
        record = self.client.getRecord(
                    metadataPrefix=metadataPrefix,
                    identifier=identifier)
        return self.process_record(record[0], record[1]._map, metadataPrefix)

    # Record search utilities

    def listRecords_or_empty(self, source, *args, **kwargs):
        """
        pyoai raises :class:`NoRecordsMatchError` when no records match,
        we would rather like to get an empty list in that case.
        """
        try:
            return source.listRecords(*args, **kwargs)
        except NoRecordsMatchError:
            return []

    def process_record(self, header, metadata, format):
        """
        Saves the record given by the header and metadata (as returned by
        pyoai) into a Paper, or None if anything failed.
        """
        translator = self.translators.get(format)
        if translator is None:
            print("Warning: unknown metadata format %s, skipping" %
                  header.format())
            return

        paper = translator.translate(header, metadata)
        if paper is not None:
            try:
                with transaction.atomic():
                    saved = Paper.from_bare(paper)
                return saved
            except ValueError as e:
                print("Ignoring invalid paper:")
                print(header.identifier())
                print(e)

    def process_records(self, listRecords, format):
        """
        Save as :class:`Paper` all the records contained in this list
        """
        # check that we have at least one translator, otherwise
        # it's not really worth trying…
        if not self.translators:
            raise ValueError("No OAI translators have been set up: " +
                             "We cannot save any record.")

        last_report = datetime.now()
        processed_since_report = 0

        with ParallelGenerator(listRecords, max_lookahead=1000) as g:
            for record in g:
                header = record[0]
                metadata = record[1]._map

                self.process_record(header, metadata, format)

                # rate reporting
                processed_since_report += 1
                if processed_since_report >= 1000:
                    td = datetime.now() - last_report
                    rate = 'infty'
                    if td.seconds:
                        rate = str(processed_since_report / td.seconds)
                    print("current rate: %s records/s" % rate)
                    processed_since_report = 0
                    last_report = datetime.now()
