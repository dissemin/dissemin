import pytest

from deposit.models import DefaultLicense
from deposit.models import License
from deposit.models import Repository

class TestLicense():
    """
    A class to test all license relevant things
    """

    def test_str(self, db):
        """
        Output of __str__ should be name (identifier)
        """
        name = "Test License"
        identifier = 'tl'
        uri = "https:/dissem.in/deposit/license/test/"
        license = License.objects.create(name=name, identifier=identifier, uri=uri)
        assert license.__str__() == name + " (" + identifier + ")"

class TestDefaultLicense():
    """
    A class to test all default license relevant things
    """
    pass
