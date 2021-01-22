import pytest

from django.contrib import auth

class TestShibbolethRemoteUserMiddleware:
    """
    We only test the one case, were the user is authenticated and has a shibboleth account
    """

    @pytest.mark.usefixtures('db')
    def test_is_authenticated(self, client, shib_request):
        """
        Thing is: When the user is authenticated, there is little differenc ein result if he hasn't been authenticated. But django changes CSRF token after login, so we can compare that.
        """

        # We are not authenticated, but if we provide the correct headers, this happens
        r = client.get('/', **shib_request)
        # Now, if we hit again and we are still logged in, this is fine
        s = client.get('/', **shib_request)
        assert r.cookies['csrftoken'] == s.cookies['csrftoken']

    @pytest.mark.usefixtures('db')
    def test_is_authenticated_no_remote_user_header(self, client, shib_request):
        """
        If we are authenticated with shibboleth, but the REMOTE_USER is missing, we want the user being logged out
        """
        client.get('/', **shib_request)
        user = auth.get_user(client)
        assert user.is_authenticated
        # Now we do the same thing. We expect, that the user is no longer logged in
        client.get('/')
        user = auth.get_user(client)
        assert not user.is_authenticated

    def test_ist_authenticated_other_auth(self, authenticated_client, django_user_model):
        """
        If we log in in any other way and have no REMOTE_USER, wo do not want to be locked out
        """
        user = auth.get_user(authenticated_client)
        assert user.is_authenticated
        authenticated_client.get('/')
        user = auth.get_user(authenticated_client)
        assert user.is_authenticated
