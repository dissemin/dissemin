import pytest


@pytest.fixture(params=[True, False])
def dummy_repository(request, dummy_repository):
    dummy_repository.enabled = request.param
    dummy_repository.save()
    return dummy_repository
