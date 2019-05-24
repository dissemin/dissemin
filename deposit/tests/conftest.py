import pytest

from deposit.models import UserPreferences


@pytest.fixture
def empty_user_preferences(db, herbert_quain):
    """
    Returns an empty UserPreferences object
    """
    user_prefs, unused = UserPreferences.objects.get_or_create(user=herbert_quain)
    yield user_prefs
    user_prefs.delete()
