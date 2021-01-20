import pytest

from datetime import date

from urllib.parse import parse_qs
from urllib.parse import urlparse
from urllib.parse import urlunparse

from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site

from deposit.models import DepositRecord
from website.forms import StartPageSearchForm
from upload.models import UploadedPDF


class TestMiscPages():
    """
    Tests various more or less static pages
    """

    @pytest.mark.parametrize('page', ['faq', 'tos', 'sources', 'account-login', 'socialaccount_login_error',])
    @pytest.mark.usefixtures('db')
    def test_static(self, page, check_page):
        """
        Tests above static pages
        """
        check_page(200, page)

    @pytest.mark.urls('website.tests.urls')
    def test_error(self, check_page):
        check_page(200, 'error')


class TestStartPageView():
    """
    This tests the start page
    """
    def test_start_page(self, db, check_page, dummy_repository, book_god_of_the_labyrinth, user_leibniz):
        """
        Validates html of start page
        """
        pdf = UploadedPDF.objects.create(
            user=user_leibniz,
            file='spam.pdf',
        )
        DepositRecord.objects.create(
            paper=book_god_of_the_labyrinth,
            user=user_leibniz,
            repository=dummy_repository,
            status='published',
            pub_date=date.today(),
            file=pdf,
        )
        check_page(200, 'start-page')

    def test_start_page_context(self, db, dissemin_base_client, dummy_repository, book_god_of_the_labyrinth, user_leibniz):
        """
        Check context data
        """
        pdf = UploadedPDF.objects.create(
            user=user_leibniz,
            file='spam.pdf',
        )
        DepositRecord.objects.create(
            paper=book_god_of_the_labyrinth,
            user=user_leibniz,
            repository=dummy_repository,
            status='published',
            pub_date=date.today(),
            file=pdf,
        )

        r = dissemin_base_client.get(reverse('start-page'))

        assert isinstance(r.context.get('search_form'), StartPageSearchForm)
        assert isinstance(r.context.get('combined_status'), list)

        latest_deposits = r.context.get('latest_deposits')
        assert len(latest_deposits) <= 5
        for d in latest_deposits:
            assert d.status == 'published'


class TestLogout:
    """
    Here we test the logout view
    """

    def test_logout_view(self, client):
        url = reverse('account-logout')
        r = client.get(url)
        assert r.status_code == 302
        assert r.url == reverse('start-page')

    def test_logout_view_shibboleth(self, client, db, settings):
        settings.SHIBBOLETH_LOGOUT_URL= 'https://sp.dissem.in/Shibboleth.sso/Logout'
        url = reverse('account-logout')
        r = client.get(url)
        assert r.status_code == 302
        parts = urlparse(r.url)
        params = parse_qs(parts.query)
        assert settings.SHIBBOLETH_LOGOUT_URL == urlunparse([parts.scheme, parts.netloc, parts.path, '','',''])
        assert params.get('return')[0] == 'https://{}'.format(get_current_site(r.request)) + reverse('start-page')
