import pytest

from backend.pubtype_translations import CITEPROC_PUBTYPE_TRANSLATION
from backend.pubtype_translations import OAI_PUBTYPE_TRANSLATIONS
from backend.pubtype_translations import SET_TO_PUBTYPE
from papers.baremodels import PAPER_TYPE_CHOICES

PAPER_TYPES = [key for key, value in PAPER_TYPE_CHOICES]

@pytest.mark.parametrize('translation', [CITEPROC_PUBTYPE_TRANSLATION, OAI_PUBTYPE_TRANSLATIONS, SET_TO_PUBTYPE])
def test_translations(translation):
    """
    Each value must be in PAPER_TYPES
    """
    for value in translation.values():
        assert value in PAPER_TYPES
