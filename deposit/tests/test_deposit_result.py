import pytest

from deposit.models import DEPOSIT_STATUS_CHOICES
from deposit.protocol import DepositResult


class TestDepositResult():
    """
    Tests around the deposit result
    """
    def test_init_invalid_status(self):
        """
        Must raise exception invalid value
        """
        key = 'spam'
        if 'spam' in [x[0] for x in DEPOSIT_STATUS_CHOICES]:
            raise Exception('{} must not be DEPOSIT_STATUS_CHOICES to have valid test'.format(key))
        with pytest.raises(ValueError):
            DepositResult(status=key)

    def test_init(self):
        d = DepositResult(status='pending')
        attributes = [
            'identifier',
            'splash_url',
            'pdf_url',
            'logs',
            'status',
            'message',
            'license',
            'oairecord',
            'embargo_date',
            'additional_info',
        ]

        assert set(attributes) == set(d.__dict__)
