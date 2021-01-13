import pytest
from django.core.management import call_command

from papers.models import Institution
from papers.models import Department
from backend.orcid import OrcidPaperSource

@pytest.fixture(scope='class')
def fetch_crossref_profile(request, django_db_setup, django_db_blocker, get_researcher_by_name):
    with django_db_blocker.unblock():
        call_command('loaddata', 'test_dump.json')
        self = request.cls
        self.i = Institution.objects.get(name='ENS')
        self.d = Department.objects.get(name='Chemistry dept')
        self.r2 = get_researcher_by_name('Ludovic', 'Jullien')
        self.r3 = get_researcher_by_name('Antoine', 'Amarilli')

        cr_api = OrcidPaperSource()
        cr_api.fetch_and_save(request.cls.r3)
