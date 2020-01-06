import os
import pytest
import responses
import zipfile

from urllib.parse import parse_qs
from urllib.parse import urlparse

from django.conf import settings

from papers.models import Researcher
from publishers.models import AliasPublisher
from publishers.models import Journal
from publishers.models import Publisher

@pytest.fixture
def affiliations():
    """
    Returns a simple list of affiliations used in cireproc
    """
    return ['University of Dublin', 'College Calvin']

@pytest.fixture
def container_title():
    """
    Returns the title. Main reason is simpler test handling for CrossRef
    """
    return 'The Infinite Library'

@pytest.fixture
def issn():
    """
    Returns a (valid) ISSN
    """
    return '1234-5675'

@pytest.fixture
def orcids():
    """
    Returns a simple of ORCIDs used in citeproc
    """
    return ['0000-0001-8187-9704', None]

@pytest.fixture
def title():
    """
    Returns the title. Main reason is simpler test handling for CrossRef
    """
    return 'The God of the Labyrinth'

@pytest.fixture
def citeproc(affiliations, container_title, issn, orcids, title):
    """
    Imaginary, yet complete citeproc example.
    Use this, to check different behaviour, by adding, deleting or modifying content.
    """
    d = {
        'abstract' : 'A detective story',
        'author' : [
            {
                'given' : 'Herbert',
                'family' : 'Quain',
                'affiliation' : [
                    {
                        'name' : affiliations[0]
                    }
                ],
                'ORCID' : orcids[0]
            },
            {
                'given' : 'Jorge Luis',
                'family' : 'Borges',
                'affiliation' : [
                    {
                        'name' : affiliations[1]
                    }
                ],
                'ORCID' : orcids[1]
            },
        ],
        'container-title' : container_title,
        'DOI' : '10.0123/quain-1933',
        'ISSN' : [
            issn,
        ],
        'issue' : '1',
        'issued' : {
            'date-parts' : [
                [
                    2019,
                    10,
                    10
                ]
            ],
        },
        'page' : 'p. 327',
        'publisher' : 'Editorial Sur',
        'title' : title,
        'type' : 'book',
        'volume' : '1',
    }

    return d

@pytest.fixture
def mock_journal_find(monkeypatch):
    """
    Mocks Publisher to return no object on calling find
    """
    monkeypatch.setattr(Journal, 'find', lambda issn, title: None)

@pytest.fixture
def mock_publisher_find(monkeypatch):
    """
    Mocks Publisher to return no object on calling find
    """
    monkeypatch.setattr(Publisher, 'find', lambda x: None)

@pytest.fixture
def mock_alias_publisher_increment(monkeypatch):
    """
    Monkeypatch this function to mit DB access
    """
    monkeypatch.setattr(AliasPublisher, 'increment', lambda x,y: True)


@pytest.fixture
def rsps_fetch_day(requests_mocker):
    """
    Mocks the fetching of a day from CrossRef
    """
    # Open zipfile with fixtures
    f_path = os.path.join(settings.BASE_DIR, 'backend', 'tests', 'data', 'crossref.zip')
    zf = zipfile.ZipFile(f_path)

    # Dynamic callback, response only depends on cursor
    def request_callback(request):
        called_url = request.url
        query = parse_qs(urlparse(called_url).query)
        cursor = query['cursor'][0]
        if cursor == '*':
            cursor = 'initial'
        f_name = '{}.json'.format(cursor)
        body = zf.read(f_name)
        return (200, {}, body)

    mock_url = 'https://api.crossref.org/works'

    # Mocking the requests
    requests_mocker.add_callback(
        responses.GET,
        mock_url,
        callback=request_callback,
    )
    return requests_mocker


@pytest.fixture
def researcher_lesot(django_user_model):
    """
    The Researcher Marie-Jeanne Lesot from doi 10.1016/j.ijar.2017.06.011
    """
    u = django_user_model.objects.create(
        username='lisotm',
        first_name='Marie-Jeanne',
        last_name='Lesot',
    )

    r = Researcher.create_by_name(
        first=u.first_name,
        last=u.last_name,
        user=u,
        orcid='0000-0002-3604-6647',
    )

    return r
