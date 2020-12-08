import pytest

from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.models import SocialLogin


@pytest.fixture
def social_login():
    account = SocialAccount(uid='0000-0001-7935-7720')
    login = SocialLogin(account=account)

    return login
