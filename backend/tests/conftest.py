import pytest

@pytest.fixture
def affiliations():
    """
    Returns a simple list of affiliations used in cireproc
    """
    return ['University of Dublin', 'College Calvin']

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
def citeproc(affiliations, orcids, title):
    """
    Imaginary, yet complete citeproc example.
    Use this, to check different behaviour, by adding, deleting or modifying content.
    """
    d = {
        'title' : title,
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
        'issued' : {
            'date-parts' : [
                2019,
                10,
                10
            ],
        },
    }

    return d
