import pytest

from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialAccount

from papers.models import Paper
from papers.models import Researcher
from website.models import ShibbolethUser
from website.signals import fetch_on_orcid_login
from website.signals import complete_researcher_profile_on_orcid_login

@pytest.mark.usefixtures('db')
class TestFetchOnORCIDLogin:

    @pytest.mark.usefixtures('mock_pub_orcid')
    def test_success(self, social_login):
        fetch_on_orcid_login(sender='test', sociallogin=social_login)
        # If we can get a researcher without exception, it does exist
        Researcher.objects.get(orcid=social_login.account.uid)

    def test_invalid_orcid(self, rf, social_login):
        social_login.account.uid = 'invalid orcid'
        with pytest.raises(ImmediateHttpResponse):
            fetch_on_orcid_login(sender='test', sociallogin=social_login, request=rf.get('/spam'))

    @pytest.mark.usefixtures('mock_pub_orcid')
    def test_no_name(self, rf, social_login):
        social_login.account.uid = '0000-0002-6091-2701'
        with pytest.raises(ImmediateHttpResponse):
            fetch_on_orcid_login(sender='test', sociallogin=social_login, request=rf.get('/spam'))


class TestCompleteResearcherProfileOnORCIDLogin:

    orcid = '0000-0001-7935-7720'

    @pytest.fixture(autouse=True)
    def setup(self, django_user_model):
        self.user = django_user_model.objects.create(username='delpeucha')
        self.account = SocialAccount.objects.create(uid=self.orcid, user=self.user)
        self.r = Researcher.get_or_create_by_orcid(self.orcid)

    @pytest.mark.usefixtures('mock_pub_orcid', 'mock_doi')
    def test_researcher_user_empty(self):
        """
        The researcher does not have a user yet, this is simple
        """
        complete_researcher_profile_on_orcid_login(sender='test', user=self.user)
        complete_researcher_profile_on_orcid_login(sender='test', user=self.user)
        self.r.refresh_from_db()
        assert self.r.user == self.user
        assert Paper.objects.all() .count() == 3

    @pytest.mark.usefixtures('mock_pub_orcid', 'mock_doi')
    def test_researcher_user_orcid(self):
        """
        The researcher has an ORCID authenticated (or other) user
        """
        self.r.user = self.user
        self.r.save()
        complete_researcher_profile_on_orcid_login(sender='test', user=self.user)
        self.r.refresh_from_db()
        assert self.r.user == self.user
        assert Paper.objects.all() .count() == 3

    def test_researcher_user_shibboleth(self, django_user_model):
        """
        Here we do have a shibboleth user attached to the researcher
        We need to merge the user, change the concordance in ShibbolethUser and delete the no longer used user
        """
        shib_user = django_user_model.objects.create(username='delpeucha_shib')
        shib_account = ShibbolethUser.objects.create(user=shib_user, shib_username='delpeucha@idp.dissem.in')
        self.r.user = shib_user
        self.r.save()
        complete_researcher_profile_on_orcid_login(sender='test', user=self.user)
        self.r.refresh_from_db()
        shib_account.refresh_from_db()
        assert self.r.user == self.user
        assert shib_account.user == self.user
        assert Paper.objects.all() .count() == 3
        assert django_user_model.objects.all().count() == 1
