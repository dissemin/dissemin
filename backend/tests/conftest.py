import pytest

@pytest.fixture
def citeproc():
    """
    Imaginary, yet complete citeproc example.
    Use this, to check different behaviour, by adding, deleting or modifying content.
    """
    d = {
        'title' : 'The God of the Labyrinth',
    }

    return d
