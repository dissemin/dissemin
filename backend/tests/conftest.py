import pytest

@pytest.fixture
def affiliation():
    """
    Returns a simple list of affiliations used in cireproc
    """
    return ['University of Dublin', 'College Calvin']

@pytest.fixture
def orcid():
    """
    Returns a simple of ORCIDs used in citeproc
    """
    return ['0000-0001-8187-9704', None]

@pytest.fixture
def citeproc(affiliation, orcid):
    """
    Imaginary, yet complete citeproc example.
    Use this, to check different behaviour, by adding, deleting or modifying content.
    """
    d = {
        'title' : 'The God of the Labyrinth',
        'author' : [
            {
                'given' : 'Herbert',
                'family' : 'Quain',
                'affiliation' : [
                    {
                        'name' : affiliation[0]
                    }
                ],
                'ORCID' : orcid[0]
            },
            {
                'given' : 'Jorge Luis',
                'family' : 'Borges',
                'affiliation' : [
                    {
                        'name' : affiliation[1]
                    }
                ],
                'ORCID' : orcid[1]
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
