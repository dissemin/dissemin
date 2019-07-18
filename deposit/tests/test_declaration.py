import inspect
import pytest

from deposit.declaration import REGISTERED_DECLARATION_FUNCTIONS
from deposit.declaration import get_declaration_function




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
