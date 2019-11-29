import pytest

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
                2019,
                10,
                10
            ],
        },
        'pages' : 'p. 327',
        'title' : title,
        'volume' : '1',
    }

    return d
