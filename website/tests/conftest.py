import pytest

@pytest.fixture
def shib_meta():
    SHIB_META = {
        'username' : 'vimess@discworld.edu',
        'first_name' : 'Samuel',
        'last_name' : 'Vimes',
        'orcid' : '0000-0001-8187-9704',
        'email' : 'vimess@discworld.edu',
    }
    return SHIB_META
