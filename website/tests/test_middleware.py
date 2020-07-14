from django.contrib import auth
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware

from papers.models import Researcher
from website.middleware import ShibbolethRemoteUserMiddleware
from website.models import ShibbolethUser

class TestShibbolethRemoteUserMiddleware:
    """
    We only test the one case, were the user is authenticated and has a shibboleth account
    """

    def test_is_authenticated(self, monkeypatch, django_user_model, rf, shib_meta):
        monkeypatch.setattr(ShibbolethRemoteUserMiddleware, 'parse_attributes', lambda x, y: (shib_meta, None))
        user = django_user_model.objects.create(
            username='vimess',
            first_name='Samuel',
            last_name='Vimes',
        )
        ShibbolethUser.objects.create(
            user=user,
            shib_username=shib_meta.get('username')
        )
        Researcher.create_by_name(shib_meta.get('first_name'), shib_meta.get('last_name'), user=user)
        # We want to build a request

        # Let's authenticate the user, because we rely on that
        user = auth.authenticate(remote_user=shib_meta.get('username'), shib_meta=shib_meta)
        request = rf.get('/', REMOTE_USER=shib_meta.get('username'))
        request.user = user
        SessionMiddleware().process_request(request)
        AuthenticationMiddleware().process_request(request)
        ShibbolethRemoteUserMiddleware().process_request(request)
        assert 'shib' in request.session
        assert request.user.is_authenticated
        assert request.user == user
