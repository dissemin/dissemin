import pytest

from backend.conftest import load_test_data as papers_load_test_data

from deposit.models import License

load_test_data = papers_load_test_data

@pytest.fixture()
def license_standard(db):
    """
    Returns a standard test license
    """

    license = License.objects.get_or_create(
        name="Standard License",
        uri="https://dissem.in/deposit/license/standard"
    )

    return license

@pytest.fixture()
def license_alternative(db):
    """
    Returns an alternative test license
    Use this license, if you need two of them
    """

    license = License.objects.get_or_create(
        name="Alternative License",
        uri="https://dissem.in/deposit/license/alternative"
    )

    return license

