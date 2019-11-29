import pytest

@pytest.fixture
def affiliation():
    """
    Returns a simple list of affiliations used in cireproc
    """
    return ['University of Dublin', 'College Calvin']

@pytest.fixture
def citeproc(affiliation):
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
                ]
            },
            {
                'given' : 'Jorge Luis',
                'family' : 'Borges',
                'affiliation' : [
                    {
                        'name' : affiliation[1]
                    }
                ]
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
