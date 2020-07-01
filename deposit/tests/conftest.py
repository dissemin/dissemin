import pytest

from deposit.models import DepositRecord
from deposit.models import LetterOfDeclaration
from papers.models import Researcher


@pytest.fixture
def lod_env(request, db, book_god_of_the_labyrinth, authenticated_client, dummy_repository, uploaded_pdf):
    """
    Everything you need for Letter of Declaration
    """
    loc = LetterOfDeclaration.objects.create(
        function_key= 'test_pdf_generator'
    )
    dummy_repository.letter_declaration = loc
    dummy_repository.save()

    user = authenticated_client.user
    user.first_name = 'Jose'
    user.last_name = 'Saramago'
    user.save()

    dr = DepositRecord.objects.create(
        paper=book_god_of_the_labyrinth,
        user=user,
        repository=dummy_repository,
        status='pending',
        file=uploaded_pdf,
    )

    Researcher.create_by_name(
        first=user.first_name,
        last=user.last_name,
        orcid="2543-2454-2345-234X",
        user=user,
    )

    request.cls.dr = dr
    request.cls.client = authenticated_client


@pytest.fixture
def dummy_deposit_record(book_god_of_the_labyrinth, user_leibniz, dummy_repository, uploaded_pdf):
    """
    Dummy deposit record with minimal information
    """

    dr = DepositRecord.objects.create(
        paper=book_god_of_the_labyrinth,
        user=user_leibniz,
        repository=dummy_repository,
        file=uploaded_pdf
    )

    return dr
