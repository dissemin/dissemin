import pytest

from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile

from deposit.models import Repository
from deposit.models import UserPreferences
from papers.baremodels import PAPER_TYPE_CHOICES
from papers.models import OaiSource

@pytest.fixture()
def simple_logo():
    """
    Fixture for a simple png image for repositories
    """
    # 1x1 px image
    simple_png_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x07tIME\x07\xdf\n\x12\x0c+\x19\x84\x1d/"\x00\x00\x00\x19tEXtComment\x00Created with GIMPW\x81\x0e\x17\x00\x00\x00\x0cIDAT\x08\xd7c\xa8\xa9\xa9\x01\x00\x02\xec\x01u\x90\x90\x1eL\x00\x00\x00\x00IEND\xaeB`\x82'
    logo = InMemoryUploadedFile(
        BytesIO(simple_png_image),
        None,
        'logo.png',
        'image/png', 
        len(simple_png_image),
        None,
        None
    )
    return logo

@pytest.fixture()
def dummy_oaisource(db):
    """
    Provides a dummy OaiSource if you just need a OaiSource, but do not do anything with it
    """
    oaisource, unused= OaiSource.objects.get_or_create(
        identifier='oai:miniaml-test',
        name='Minimal OaiSource',
        default_pubtype=PAPER_TYPE_CHOICES[0][0],
    )
    yield oaisource
    oaisource.delete()


@pytest.fixture()
def dummy_repository(db, simple_logo, dummy_oaisource):
    """
    Returns a dummy_repository with a faked dummy-protocol where you need only the repository, but do not anything with it.
    """
    repo, unused = Repository.objects.get_or_create(
        name='Dummy Test Repository',
        description='Test repository',
        protocol='No-Protocol',
        oaisource=dummy_oaisource
    )
    yield repo
    repo.delete()

@pytest.fixture()
def herbert_quain(db):
    user = User.objects.create_user(
        username='quain',
        first_name='Herbert',
        last_name='Quain',
        email='herbert.quain@writers.ir',
    )
    yield user
    user.delete()

@pytest.fixture()
def empty_user_preferences(db, herbert_quain):
    """
    Returns an empty UserPreferences object
    """
    user_prefs, unused = UserPreferences.objects.get_or_create(user=herbert_quain)
    yield user_prefs
    user_prefs.delete()
