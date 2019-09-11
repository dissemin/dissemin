import inspect
import pytest

from deposit.declaration import REGISTERED_DECLARATION_FUNCTIONS
from deposit.declaration import get_declaration_function
from deposit.models import License




class TestDeclarations():
    """
    Class that groups tests for declarations.
    """

    @pytest.mark.parametrize('func_name', [key for key in REGISTERED_DECLARATION_FUNCTIONS.keys()])
    def test_get_declaration_creator(self, func_name):
        """
        Test to verify return of correct function
        """
        func = get_declaration_function(func_name)
        assert inspect.isfunction(func)
        assert func.__name__ == func_name


    def test_get_declaration_func_not_found(self, monkeypatch):
        """
        Expecting `None` if no function is returned
        """
        with pytest.raises(AttributeError):
            get_declaration_function('spam')

@pytest.mark.usefixtures('deposit_record')
class TestDeclarationLetters():
    """
    Class that groups test for generating letter of deposits.
    """
    def test_declaration_ulb_darmststadt(self):
        """
        This tests the letter of declaration for ULB Darmstadt.
        """
        self.dr.repository.letter_declaration = 'declaration_ulb_darmstadt'
        self.dr.repository.save()

        self.dr.license = License.objects.all().first()
        self.dr.identifier = '5732'
        self.dr.save()

        self.client.user.first_name = 'Jose'
        self.client.user.last_name = 'Saramago'

        func = get_declaration_function(self.dr.repository.letter_declaration)

        func(self.dr, self.client.user)
