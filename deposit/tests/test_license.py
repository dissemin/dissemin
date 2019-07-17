import pytest
from deposit.models import License

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
        license = License.objects.create(name=name, uri=uri)
        assert license.__str__() == name


@pytest.mark.skip(reason="Fixtures not yet implemented")
class TestLicenseChooser():
    """
    A class to test LicenseChooser model
    """
    pass


