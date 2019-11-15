import pytest

from datetime import date

from django.urls import reverse

from deposit.models import DepositRecord
from dissemin.forms import StartPageSearchForm
from upload.models import UploadedPDF


class TestMiscPages():
    """
    Tests various more or less static pages
    """

    @pytest.mark.parametrize('page', ['faq', 'tos', 'sources', 'account-login', 'socialaccount_login_error',])
    def test_static(self, page, check_page):
        """
        Tests above static pages
        """
        check_page(200, page)



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

        assert isinstance(r.context.get('search_form'), StartPageSearchForm) == True
        assert isinstance(r.context.get('combined_status'), list) == True

        latest_deposits = r.context.get('latest_deposits')
        assert len(latest_deposits) <= 5
        for d in latest_deposits:
            assert d.status == 'published'
