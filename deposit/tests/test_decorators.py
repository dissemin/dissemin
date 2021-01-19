from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse

from deposit.decorators import shib_meta_to_user
from website.middleware import ShibbolethRemoteUserMiddleware

class TestShibMetaToUser:

    def test_with_values(self, db, monkeypatch, rf, shib_meta):
        monkeypatch.setattr(ShibbolethRemoteUserMiddleware, 'parse_attributes', lambda x, y: (shib_meta, None))
        request = rf.get('/', REMOTE_USER=shib_meta.get('username'))
        SessionMiddleware().process_request(request)
        AuthenticationMiddleware().process_request(request)
        ShibbolethRemoteUserMiddleware().process_request(request)

        # Let's test the decorator
        @shib_meta_to_user
        def sample_view(request):
            # Let's check the attribute
            assert request.user.shib == shib_meta
            return HttpResponse()
        response = sample_view(request)
        assert response.status_code == 200

    def test_without_values(self, rf):
        request = rf.get('/')
        SessionMiddleware().process_request(request)
        AuthenticationMiddleware().process_request(request)

        # Let's test the decorator
        @shib_meta_to_user
        def sample_view(request):
            # Let's check the attribute
            assert request.user.shib =={}
            return HttpResponse()
        response = sample_view(request)
        assert response.status_code == 200
