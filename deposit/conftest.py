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


# This is a list of oairecords to be tested
metadata_publications = [
    'book_god_of_the_labyrinth',
    'other_assisting_configuration_based_feature_model_composition',
]


@pytest.fixture(params=metadata_publications)
def publication(request, load_json):
    """
    Loads the above list of OaiRecords and corresponding Papers one after the other and returns the Paper object
    """
    return load_json.load_oairecord(request.param)[0]
