import pytest

from django.contrib import auth

from papers.models import Researcher
from website.models import ShibbolethUser

@pytest.mark.usefixtures('db')
class TestShibbolethRemoteUserBackendExistingShibbolethUser:
    """
    Test class to test ShibbolethRemoteUserBackend where the user exists as ShibbolethUser
    """

    @pytest.fixture(autouse=True)
    def preparation(self, django_user_model, shib_meta):
        self.shib_meta = shib_meta
        self.remote_user = self.shib_meta.get('username')
        # Adding a ShibbolethUser and a researcher. The latter exists since the first exists
        self.user = django_user_model.objects.create_user('vimess')
        self.shib_user = ShibbolethUser.objects.create(user=self.user, shib_username=self.shib_meta.get('username'))
        self.researcher = Researcher.create_by_name(
            self.shib_meta.get('first_name'),
            self.shib_meta.get('last_name'),
            orcid=self.shib_meta.get('orcid'),
            user=self.user
        )

    def assert_shibboleth_md(self, user):
        assert user.first_name == self.shib_meta.get('first_name')
        assert user.last_name == self.shib_meta.get('last_name')

    def test_authenticate_no_orcid(self):
        del self.shib_meta['orcid']
        user = auth.authenticate(remote_user=self.remote_user, shib_meta=self.shib_meta)
        assert user.shibbolethuser == self.shib_user
        assert user == self.researcher.user
        #self.assert_shibboleth_md(user, self.shib_meta)

    def test_authenticate_orcid_identical(self):
        user = auth.authenticate(remote_user=self.remote_user, shib_meta=self.shib_meta)
        self.researcher.refresh_from_db()
        assert user.shibbolethuser == self.shib_user
        assert user == self.researcher.user
        assert self.researcher.orcid == self.shib_meta.get('orcid')

    def test_researcher_has_no_orcid(self):
        self.researcher.orcid = ''
        self.researcher.save()
        user = auth.authenticate(remote_user=self.remote_user, shib_meta=self.shib_meta)
        self.researcher.refresh_from_db()
        assert user.shibbolethuser == self.shib_user
        assert user == self.researcher.user
        assert self.researcher.orcid== self.shib_meta.get('orcid')

    def test_alt_researcher_with_user(self, django_user_model):
        self.researcher.orcid = ''
        self.researcher.save()
        u2 = django_user_model.objects.create_user('vimess2')
        r2 = Researcher.create_by_name('Samuel', 'Vimes', orcid=self.shib_meta.get('orcid'), user=u2)
        user = auth.authenticate(remote_user=self.remote_user, shib_meta=self.shib_meta)
        self.researcher.refresh_from_db()
        assert self.researcher.orcid == self.shib_meta.get('orcid')
        with pytest.raises(Researcher.DoesNotExist):
            r2.refresh_from_db()
        assert user.shibbolethuser == self.shib_user
        assert user == self.researcher.user
        with pytest.raises(django_user_model.DoesNotExist):
            u2.refresh_from_db()


    def test_alt_researcher_without_user(self):
        self.researcher.orcid = ''
        self.researcher.save()
        r2 = Researcher.create_by_name('Samuel', 'Vimes', orcid=self.shib_meta.get('orcid'))
        user = auth.authenticate(remote_user=self.remote_user, shib_meta=self.shib_meta)
        self.researcher.refresh_from_db()
        assert self.researcher.orcid == self.shib_meta.get('orcid')
        with pytest.raises(Researcher.DoesNotExist):
            r2.refresh_from_db()
        assert user.shibbolethuser == self.shib_user
        assert user == self.researcher.user


@pytest.mark.usefixtures('db')
class TestShibbolethRemoteUserBackendNewShibbolethUser:
    """
    Test class to test ShibbolethRemoteUserBackend where the user does not exist as ShibbolethUser
    """

    @pytest.fixture(autouse=True)
    def preparation(self, shib_meta):
        self.shib_meta = shib_meta
        self.remote_user = self.shib_meta.get('username')

    def test_authenticate_no_orcid(self):
        """
        ShibbolethUser does not exist and has no ORCID
        """
        del self.shib_meta['orcid']
        user = auth.authenticate(remote_user=self.remote_user, shib_meta=self.shib_meta)
        assert user.username == self.shib_meta.get('username')
        assert user.shibbolethuser.shib_username == self.shib_meta.get('username')
        r = Researcher.objects.get(user=user)
        assert r.orcid is None

    def test_authenticate_orcid_not_found(self):
        """
        ShibbolethUser does not exist, no Researcher has this ORCID
        """
        user = auth.authenticate(remote_user=self.remote_user, shib_meta=self.shib_meta)
        assert user.username == self.shib_meta.get('username')
        assert user.shibbolethuser.shib_username == self.shib_meta.get('username')
        r = Researcher.objects.get(user=user)
        assert r.orcid == self.shib_meta.get('orcid')

    def test_authenticate_researcher_with_user(self, django_user_model):
        user = django_user_model.objects.create_user('vimess')
        r = Researcher.create_by_name(
            self.shib_meta.get('first_name'),
            self.shib_meta.get('last_name'),
            orcid=self.shib_meta.get('orcid'),
            user=user
        )
        user2 = auth.authenticate(remote_user=self.remote_user, shib_meta=self.shib_meta)
        assert user == user2
        r.refresh_from_db()
        assert r.user == user
        assert r.orcid == self.shib_meta.get('orcid')
        assert user2.shibbolethuser.shib_username == self.shib_meta.get('username')

    def test_authenticate_researcher_without_user(self):
        r = Researcher.create_by_name(
            self.shib_meta.get('first_name'),
            self.shib_meta.get('last_name'),
            orcid=self.shib_meta.get('orcid'),
        )
        user = auth.authenticate(remote_user=self.remote_user, shib_meta=self.shib_meta)
        assert user.shibbolethuser.shib_username == self.shib_meta.get('username')
        r.refresh_from_db()
        assert r.user == user
        assert r.orcid == self.shib_meta.get('orcid')
