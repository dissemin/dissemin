import pytest


@pytest.fixture(params=[True, False])
def dummy_repository(request, dummy_repository):
    dummy_repository.enabled = request.param
    dummy_repository.save()
    return dummy_repository


class TestUserPreferences():
    """
    Groups tests for model UserPreferences
    """

    def test_get_last_repository(self, dummy_repository, empty_user_preferences):
        """
        If last repository is enabled, return repository else return None and set default repository to None
        """
        empty_user_preferences.last_repository = dummy_repository
        empty_user_preferences.save()
        if dummy_repository.enabled:
            assert empty_user_preferences.get_last_repository() == dummy_repository
        else:
            assert empty_user_preferences.get_last_repository() == None
            assert empty_user_preferences.last_repository == None

    def test_get_last_repository_none(self, empty_user_preferences):
        """
        If no last repository is set, return None
        """
        assert empty_user_preferences.get_last_repository() == None

    def test_get_preferred_repository(self, dummy_repository, empty_user_preferences):
        """
        If preferred repository is enabled, return repository else return None and set default repository to None
        """
        empty_user_preferences.preferred_repository = dummy_repository
        empty_user_preferences.save()
        if dummy_repository.enabled:
            assert empty_user_preferences.get_preferred_repository() == dummy_repository
        else:
            assert empty_user_preferences.get_preferred_repository() == None
            assert empty_user_preferences.preferred_repository == None


    def test_get_preferred_repository_none(self, empty_user_preferences):
        """
        If no preferred repository is set, return None
        """
        assert empty_user_preferences.get_preferred_repository() == None

    def test_get_preferred_or_last_repository_preferred(self, dummy_repository, empty_user_preferences):
        """
        If preferred repository is set, return this or None
        """
        empty_user_preferences.preferred_repository = dummy_repository
        empty_user_preferences.save()
        assert empty_user_preferences.get_preferred_or_last_repository() == empty_user_preferences.get_preferred_repository()

    def test_get_preferred_or_last_repository_last(self, dummy_repository, empty_user_preferences):
        """
        If preferred is None or not enabled, return last repository or None
        """
        empty_user_preferences.last_repository = dummy_repository
        empty_user_preferences.save()
        assert empty_user_preferences.get_preferred_or_last_repository() == empty_user_preferences.get_last_repository()


