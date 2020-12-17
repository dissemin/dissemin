class MetadataConverter():
    """
    This class is able to convert our own metadata of a paper from the database into a relatively flat dictionary-like object

    Additionally, since there is usually more than one OaiRecord for a paper, you can set a list of prefered OaiRecords to look for information first.

    The OaiRecords are put into a list, where the prefered ones are first.
    """

    def __init__(self, paper, prefered_records=[]):
        """
        Initiates object with a paper and a list of prefered OaiRecords
        :param paper: A paper object
        :param prefered_records: Iterable of OaiRecords to investigate first for metadata
        """
        self.paper = paper
        self.records = prefered_records + [r for r in paper.oairecord_set.all() if r not in prefered_records]
        # Let's set metadata based on the given paper and its oairecords
        self.metadata = dict()
        self._paper_metadata()
        self._oai_metadata()

    def get(self, key, default=None):
        return getattr(self, key, default)

    def _oai_metadata(self):
        """
        Gets only metadata from OaiRecord objects with prefered having priority
        """
        oai_metadata = {
            'doi' : self._get_doi(),
            'essn' : self._get_essn(),
            'issn' : self._get_issn(),
            'issue' : self._get_issue(),
            'journal' : self._get_journal(),
            'pages' : self._get_pages(),
            'publisher' : self._get_publisher(),
            'romeo_id' : self._get_romeo_id(),
            'volume' : self._get_volume(),
        }

        # Now that we have all metadata, let's set them as attributes
        for key, value in oai_metadata.items():
            setattr(self, key, value)

    def _paper_metadata(self):
        """
        Gets only the metadata from the paper
        This metadata always exists
        """

        self.authors = self._get_authors()
        self.doctype = self.paper.doctype
        self.pubdate = self.paper.pubdate
        self.title = self.paper.title

    def _get_authors(self):
        """
        Returns a list of authors, containing a dict with:
        first
        last
        orcid
        """
        authors_list = [
            {
                'first' : author['name']['first'],
                'last' : author['name']['last'],
                'orcid' : author['orcid'],
            }
            for author in self.paper.authors_list
        ]

        return authors_list

    def _get_doi(self):
        """
        Gets the DOI
        :returns: DOI or None
        """
        for r in self.records:
            if r.doi:
                return r.doi

    def _get_essn(self):
        """
        Gets the ESSN / EISSN
        :returns: ESSN or None
        """
        for r in self.records:
            if r.journal and r.journal.essn:
                return r.journal.essn

    def _get_issn(self):
        """
        Gets the ISSN
        :returns: ISSN or None
        """
        for r in self.records:
            if r.journal and r.journal.issn:
                return r.journal.issn

    def _get_issue(self):
        """
        Gets the issue
        :returns: issue or None
        """
        for r in self.records:
            if r.issue:
                return r.issue

    def _get_journal(self):
        """
        Gets the title from the journal
        :returns: journal title or None
        """
        for r in self.records:
            if r.journal:
                return r.journal.title
            if r.journal_title:
                return r.journal_title

    def _get_pages(self):
        """
        Gets the pages
        :returns: pages or None
        """
        for r in self.records:
            if r.pages:
                return r.pages

    def _get_publisher(self):
        """
        Gets the name from the publisher
        :returns: publisher name or None
        """
        for r in self.records:
            if r.publisher:
                return r.publisher.name
            if r.publisher_name:
                return r.publisher_name

    def _get_romeo_id(self):
        """
        Gets the romeo id
        :returns: romeo id or None
        """
        for r in self.records:
            if r.publisher and r.publisher.romeo_id:
                return r.publisher.romeo_id

    def _get_volume(self):
        """
        Gets the volume
        :returns: volume or None
        """
        for r in self.records:
            if r.volume:
                return r.volume
