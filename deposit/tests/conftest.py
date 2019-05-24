import pytest

from deposit.models import UserPreferences


@pytest.fixture
def empty_user_preferences(db, user_isaac_newton):
    """
    Returns an empty UserPreferences object
    """
    user_prefs, unused = UserPreferences.objects.get_or_create(user=user_isaac_newton)
    yield user_prefs
    user_prefs.delete()
