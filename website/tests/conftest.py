import pytest

from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.models import SocialLogin


@pytest.fixture
def social_login():
    account = SocialAccount(uid='0000-0001-7935-7720')
    login = SocialLogin(account=account)

    return login


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
