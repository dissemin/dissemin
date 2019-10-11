import pytest

from datetime import date
from datetime import timedelta

from deposit.tasks import change_embargoed_to_published

class TestChangeEmbargoedToPublished:
    """
    Class that groups tests for change_embargoed_to_published
    """

    @pytest.mark.parametrize('status,pub_date,expected', [('embargoed', date.today(), 'published'), ('embargoed', date.today() - timedelta(days=1), 'published'), ('embargoed', date.today() + timedelta(days=1), 'embargoed')])
    def test_changed_embargoed_to_published(self,  dummy_deposit_record, status, pub_date, expected):
        """
        Test for various cases for named function
        """
        dummy_deposit_record.status = status
        dummy_deposit_record.pub_date = pub_date
        dummy_deposit_record.save()

        change_embargoed_to_published()

        dummy_deposit_record.refresh_from_db()

        assert dummy_deposit_record.status == expected
