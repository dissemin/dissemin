class TestUserPreferences():
    """
    Groups tests for model UserPreferences
    """

    def test_get_last_repository_enabled(self, dummy_repository, empty_user_preferences):
        """
        If last repository is enabled, return repository
        """
        empty_user_preferences.last_repository = dummy_repository
        empty_user_preferences.save()
        
        assert empty_user_preferences.get_last_repository() == dummy_repository


    def test_get_lastrepository_disabled(self, dummy_repository, empty_user_preferences):
        """
        If last repository is disabled, return None and set last repository to None
        """
        empty_user_preferences.last_repository = dummy_repository
        empty_user_preferences.save()
        dummy_repository.enabled = False
        dummy_repository.save()

        assert empty_user_preferences.get_last_repository() == None
        assert empty_user_preferences.last_repository == None

    def test_get_last_repository_none(self, empty_user_preferences):
        """
        If no last repository is set, return None
        """
        assert empty_user_preferences.get_last_repository() == None

    def test_get_preferred_repository_enabled(self, dummy_repository, empty_user_preferences):
        """
        If preferred repository is enabled, return repository
        """
        empty_user_preferences.preferred_repository = dummy_repository
        empty_user_preferences.save()
        
        assert empty_user_preferences.get_preferred_repository() == dummy_repository

    def test_get_preferred_repository_disabled(self, dummy_repository, empty_user_preferences):
        """
        If preferred repository is disabled, return None and set default repository to None
        """
        empty_user_preferences.preferred_repository = dummy_repository
        empty_user_preferences.save()
        dummy_repository.enabled = False
        dummy_repository.save()

        assert empty_user_preferences.get_preferred_repository() == None
        assert empty_user_preferences.preferred_repository == None

    def test_get_preferred_repository_none(self, empty_user_preferences):
        """
        If no preferred repository is set, return None
        """
        assert empty_user_preferences.get_preferred_repository() == None

