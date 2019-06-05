import json
import os
import pytest

from datetime import date
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile

from deposit.models import Repository
from papers.baremodels import PAPER_TYPE_CHOICES
from papers.models import Paper
from papers.models import OaiSource


@pytest.fixture
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


@pytest.fixture
def oaisource(db):
    """
    Returns a class from which you can create several oaisources.
    """
    class Dummy():
        """
        Dummy class to gahter different functions
        """
        def __init__(self):
            """
            List of objects that will be deleted after test is done
            """
            self.objects = []

        def dummy_oaisource(self):
            """
            Provides a dummy OaiSource if you just need a OaiSource, but do not do anything with it
            """
            oaisource, unused = OaiSource.objects.get_or_create(
                identifier='oai:dummy-test',
                name='Dummy OaiSource',
                default_pubtype=PAPER_TYPE_CHOICES[0][0],
            )
            self.objects.append(oaisource)
            return oaisource
        
        @staticmethod
        def base_oaisource():
            """
            Provides BASE OaiSource. It is in the database from a migration. We do not add it to the list of to be deleted OaiSources
            """
            return OaiSource.objects.get(identifier='base')

    dummy = Dummy()
    yield dummy
    for obj in dummy.objects:
        obj.delete()


@pytest.fixture
def dummy_oaisource(oaisource):
    """
    Provides a dummy OaiSource if you just need a OaiSource, but do not do anything with it. Use this, if you need just a single OaiSource.
    """
    return oaisource.dummy_oaisource()

@pytest.fixture
def repository(db, simple_logo, oaisource):
    """
    Returns a class from which you can create several repositories. Use if you need more than one repository.
    """
    class Dummy():
        """
        Dummy class to gather the different functions.
        """
        def __init__(self):
            self.objects = []

        def dummy_repository(self):
            """
            Returns a dummy_repository with a faked dummy-protocol where you need only the repository, but do not anything with it.
            """
            repo = Repository.objects.create(
                name='Dummy Test Repository',
                description='Test repository',
                logo=simple_logo,
                protocol='No-Protocol',
                oaisource=oaisource.dummy_oaisource(),
            )
            self.objects.append(repo)
            return repo

        def sword_mets_repository(self):
            """
            Returns a new SWORD METS repository using SWORDMETSProtocol. SWORDMETSProtocol is an abstract class, so you can't really do anything with it and this repository.
            """
            repo = Repository.objects.create(
                name='Repository SWORD METS',
                description='SOWRD METS Test repository',
                logo=simple_logo,
                username='dissemin',
                password='dissemin',
                protocol='SWORDMETSProtocol',
                endpoint='https://deposit.dissem.in/sword_mets/',
                oaisource=oaisource.dummy_oaisource(),
            )
            self.objects.append(repo)
            return repo

    dummy = Dummy()
    yield dummy
    for obj in dummy.objects:
        obj.delete()


@pytest.fixture
def dummy_repository(repository):
    """
    Returns a dummy_repository with a faked dummy-protocol where you need only the repository, but do not anything with it. Use this if you need a single dummy repository.
    """
    return repository.dummy_repository()


@pytest.fixture
def book_god_of_the_labyrinth(db):
    """
    Returns a paper, type book
    """
    Paper.objects.get_or_create(
        title = "The God of the Labyrinth",
        fingerprint = 'the-god-of-thy-labyrinth',
        pubdate = date(year=1933, month=1, day=1),
        authors_list = '{ "first":"Herbert", "last":"Quain"}',
        doctype='book',
    )



@pytest.fixture
def user_isaac_newton(db):
    """
    Returns the user Isaac Newton
    """
    user = User.objects.create_user(
        username='newton',
        first_name='Isaac',
        last_name='Newton',
        email='isaac.newton@scientists.free',
    )
    yield user
    user.delete()


@pytest.fixture(scope="class")
def blank_pdf_path():
    testdir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(testdir, 'upload', 'tests', 'data', 'blank.pdf')
    return path


@pytest.fixture(scope="class")
def blank_pdf(blank_pdf_path):
    with open(blank_pdf_path, 'rb') as f:
            pdf = f.read()
    return pdf
