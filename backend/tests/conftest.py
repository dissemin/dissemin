import pytest

@pytest.fixture
def citeproc():
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
            },
            {
                'given' : 'Jorge Luis',
                'family' : 'Borges',
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
