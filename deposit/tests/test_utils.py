import pytest

from deposit.models import UserPreferences
from deposit.utils import MetadataConverter
from deposit.utils import get_email
from deposit.utils import get_preselected_repository
from papers.models import Institution
from papers.models import OaiSource
from papers.models import OaiRecord
from papers.models import Researcher
from publishers.models import Journal
from publishers.models import Publisher

@pytest.fixture
def prefered_record(db, book_god_of_the_labyrinth):
    """
    The prefered record
    """
    prefered_source = OaiSource.objects.get(identifier='crossref')
    prefered_publisher = Publisher.objects.create(
        name='Prefered Publisher',
        romeo_id='1'
    )
    prefered_journal = Journal.objects.create(
        essn='0000-0001',
        issn='0000-0010',
        publisher=prefered_publisher,
        title='Prefered Journal',

    )
    o = OaiRecord.objects.create(
        about=book_god_of_the_labyrinth,
        doi='10.1000/prefered',
        identifier='test:prefered_record',
        issue='prefered issue',
        journal=prefered_journal,
        journal_title='Prefered Journal on Record',
        pages='S. 1-10',
        publisher=prefered_publisher,
        publisher_name='Prefered Publisher on Record',
        source=prefered_source,
        volume='prefered volume',
    )
    return o

@pytest.fixture
def alternative_record(db, book_god_of_the_labyrinth, dummy_oaisource):
    """
    A simple alternative OaiRecord
    """
    alternative_publisher = Publisher.objects.create(
        name='Alternative Publisher',
        romeo_id='2',
    )
    alternative_journal = Journal.objects.create(
        essn='0000-0002',
        issn='0000-0012',
        publisher=alternative_publisher,
        title='Alternative Journal',
    )
    o = OaiRecord.objects.create(
        about=book_god_of_the_labyrinth,
        doi='10.1000/alternative',
        identifier='test:alternative_record',
        issue='alternative issue',
        journal=alternative_journal,
        journal_title='Alternative Journal on Record',
        pages='S. 11-20',
        publisher=alternative_publisher,
        publisher_name='Alternative Publisher on Record',
        source=dummy_oaisource,
        volume='alternative volume',

    )
    return o


class TestGetEmail:
    """
    Test about getting the email of a user
    """
    email = 'test@dissem.in'

    @pytest.fixture(autouse=True)
    def setup(self, django_user_model):
        self.user = django_user_model.objects.create(username='test')

    def test_mail_from_shib(self):
        self.user.shib = {'email' : self.email}
        email = get_email(self.user)
        assert email == self.email

    def test_mail_from_preferences(self):
        UserPreferences.objects.create(user=self.user, email=self.email)
        email = get_email(self.user)
        assert email == self.email

    def test_mail_from_researcher(self):
        Researcher.create_by_name('a', 'b', user=self.user, email=self.email)
        email = get_email(self.user)
        assert email == self.email

    def test_mail_from_user(self):
        self.user.email = self.email
        email = get_email(self.user)
        assert email == self.email

    def test_no_email(self):
        email = get_email(self.user)
        assert email is None

class TestGetPreselectedRepository:

    @pytest.fixture(autouse=True)
    def setup(self, django_user_model, dummy_repository):
        self.user = django_user_model.objects.create(username='test')
        self.repository = dummy_repository
        self.repositories = [dummy_repository]

    def test_preferred_repository(self):
        UserPreferences.objects.create(user=self.user, preferred_repository=self.repository)
        assert get_preselected_repository(self.user, self.repositories) == self.repository

    def test_from_shibboleth(self, shib_meta):
        self.user.shib = shib_meta
        Institution.objects.create(
            name='Insitute',
            identifiers=['shib:{}'.format(shib_meta.get('username').split('!')[0])],
            repository=self.repository
        )
        assert get_preselected_repository(self.user, self.repositories) == self.repository

    def test_last(self):
        UserPreferences.objects.create(user=self.user, last_repository=self.repository)
        assert get_preselected_repository(self.user, self.repositories) == self.repository

    def test_none(self):
        assert get_preselected_repository(self.user, self.repositories) is None




class TestMetadataConverter():

    oairecord_keys = ['doi', 'essn', 'issn', 'issue', 'journal', 'pages', 'publisher', 'romeo_id', 'volume']
    paper_keys = ['authors', 'doctype', 'pubdate', 'title']

    @pytest.fixture(autouse=True)
    def setup(self, book_god_of_the_labyrinth, prefered_record):
        """
        Sets the MetadataConverter ready to use and gives access to prefered and alternative record.
        """
        self.rp = prefered_record
        self.mc = MetadataConverter(book_god_of_the_labyrinth)

    def test_oai_metadata(self):
        """
        Check that every key exists and has a value
        """
        oai_metadata = self.mc.oai_metadata()
        for key in self.oairecord_keys:
            assert oai_metadata.get(key) is not None

    def test_paper_metadata(self):
        """
        Check that every key exists and has a value
        """
        paper_metadata = self.mc.paper_metadata()
        for key in self.paper_keys:
            assert paper_metadata.get(key) is not None

    def test_metadata(self):
        """
        Check that keys are there
        """
        metadata = self.mc.metadata()
        for key in self.paper_keys + self.oairecord_keys:
            assert metadata.get(key) is not None


class TestMetadataConverterInit():
    """
    Groups tests about the class MetadataConverter
    """
    
    def test_init_default(self, dummy_paper, dummy_oairecord):
        """
        If no prefered_records are set, OaiRecord list is just papers set of OaiRecords
        """
        mc = MetadataConverter(dummy_paper)
        assert mc.paper == dummy_paper
        assert len(mc.records) == 1
        assert dummy_oairecord in mc.records

    def test_init_prefered_records(self, dummy_paper, dummy_oairecord, prefered_record):
        """
        Prefered must be a list containing dummy_oairecord
        """
        mc = MetadataConverter(dummy_paper, [prefered_record])
        assert mc.records[0] == prefered_record
        assert mc.records[1] == dummy_oairecord


class TestMetadataConverterOaiRecordDataCreation():
    """
    Groups tests about the class MetadataConverter that deal with creation of metadata from OaiRecords
    """

    @pytest.fixture(autouse=True)
    def setup(self, dummy_paper, dummy_oairecord, dummy_publisher, dummy_journal):
        """
        Sets the MetadataConverter ready to use and gives access to prefered and alternative record.
        """
        self.record = dummy_oairecord
        self.record.publisher = dummy_publisher
        self.record.journal = dummy_journal
        # We pass a prefered OaiRecord, so that we do not need to save
        self.mc = MetadataConverter(dummy_paper, [dummy_oairecord])

    @pytest.mark.parametrize('doi, expected', [('10.100/spam', '10.100/spam'), ('', None)])
    def test_doi(self, doi, expected):
        self.record.doi = doi
        assert self.mc._get_doi() == expected

    @pytest.mark.parametrize('essn, expected', [('0000-0000', '0000-0000'), ('', None)])
    def test_essn(self, essn, expected):
        self.record.journal.essn = essn
        assert self.mc._get_essn() == expected

    @pytest.mark.parametrize('issn, expected', [('0000-0000', '0000-0000'), ('', None)])
    def test_issn(self, issn, expected):
        self.record.journal.issn = issn
        assert self.mc._get_issn() == expected

    @pytest.mark.parametrize('issue, expected', [('issue 1', 'issue 1'), ('', None)])
    def test_issue(self, issue, expected):
        self.record.issue = issue
        assert self.mc._get_issue() == expected

    def test_journal(self):
        title = 'journal title'
        journal_title = 'another journal title'
        self.record.journal.title = title
        self.record.journal_title = journal_title
        assert self.mc._get_journal() == title

    def test_journal_no_journal(self):
        self.record.journal = None
        journal_title = 'journal title'
        self.record.journal_title = journal_title
        assert self.mc._get_journal() == journal_title

    def test_journal_no_journal_title(self):
        self.record.journal = None
        assert self.mc._get_journal() is None

    @pytest.mark.parametrize('pages, expected', [('1-10', '1-10'), ('', None)])
    def test_get_pages(self, pages, expected):
        self.record.pages = pages
        assert self.mc._get_pages() == expected

    def test_publisher(self):
        name = 'publisher name'
        publisher_name = 'another publisher name'
        self.record.publisher.name = name
        self.record.publisher_name = publisher_name
        assert self.mc._get_publisher() == name

    def test_publisher_no_publisher(self):
        self.record.publisher = None
        publisher_name = 'publisher name'
        self.record.publisher_name = publisher_name
        assert self.mc._get_publisher() == publisher_name

    def test_publisher_no_publisher_name(self):
        self.record.publisher = None
        assert self.mc._get_publisher() is None

    @pytest.mark.parametrize('romeo_id, expected', [('1', '1'), ('', None)])
    def test_romeo_id(self, romeo_id, expected):
        self.record.publisher.romeo_id = romeo_id
        assert self.mc._get_romeo_id() == expected

    @pytest.mark.parametrize('volume, expected', [('vol 10', 'vol 10'), ('', None)])
    def test_get_volume(self, volume, expected):
        self.record.volume = volume
        assert self.mc._get_volume() == expected


author_one =  [{
    'name': {
        'full': 'herbert quain',
        'first': 'Herbert',
        'last': 'Quain',
    },
    'orcid' : None
}]

author_two = [{
    'name': {
        'full': 'aristoteles',
        'first': 'Aristoteles',
        'last': 'Stageira'
    },
    'orcid': None,
}]

class TestMetadataConverterPaperDataCreation():
    """
    Groups all tests related to get data from the paper
    """

    @pytest.fixture(autouse=True)
    def setup(self, dummy_paper):
        """
        Sets the MetadataConverter ready to use
        """
        self.paper = dummy_paper
        self.mc = MetadataConverter(self.paper)

        
    @pytest.mark.parametrize('authors_list', [author_one, author_one + author_two])
    def test_get_authors(self, authors_list):
        """
        Tests if authors are generated accordingly
        """
        self.paper.authors_list = authors_list

        authors = self.mc._get_authors()

        assert isinstance(authors, list)
        assert len(authors) == len(authors_list)
        for idx, author in enumerate(authors):
            assert author['first'] == authors_list[idx]['name']['first']
            assert author['last'] == authors_list[idx]['name']['last']
            assert author['orcid'] == authors_list[idx]['orcid']


