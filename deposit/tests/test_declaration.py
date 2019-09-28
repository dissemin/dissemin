import pytest

from deposit.declaration import declaration_ulb_darmstadt
from deposit.models import License


@pytest.mark.usefixtures('deposit_record')
class TestDeclarationLetters():
    """
    Class that groups test for generating letter of deposits.
    """
    def test_declaration_ulb_darmstadt(self):
        """
        This tests the letter of declaration for ULB Darmstadt.
        """
        self.dr.repository.save()

        self.dr.license = License.objects.all().first()
        self.dr.identifier = '5732'
        self.dr.save()

        self.client.user.first_name = 'Jose'
        self.client.user.last_name = 'Saramago'

        declaration_ulb_darmstadt(self.dr, self.client.user)
