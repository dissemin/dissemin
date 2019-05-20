from deposit.models import License
from deposit.models import Repository

class TestLicense():
    """
    A class to test all license relevant things
    """

    def test_str(self, db):
        """
        Output of __str__ should be its name
        """
        name = "Test License"
        uri = "https:/dissem.in/deposit/license/test/"
        license = License.objects.create(name, uri=uri)
        assert license.__str__() == name 


class TestDefaultLicense():
    """
    A class to test all default license relevant things
    """
    pass
