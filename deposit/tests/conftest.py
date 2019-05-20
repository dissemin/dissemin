import pytest

from deposit.models import License

@pytest.fixture()
def license_test(db):
    """
    Returns a standard test license
    """
    
    license = License.objects.create(name="Test License", identifier='tl', uri="https://dissem.in/deposit/license/test")

    return license


