import pytest
from django.core.management import call_command

from papers.models import OaiSource
from papers.models import Department
from papers.models import Institution
from backend.tests.test_generic import get_researcher_by_name
from publishers.models import Journal

@pytest.fixture
def load_test_data(request, db, django_db_setup, django_db_blocker):
    rebuild_index = (
        lambda: call_command('rebuild_index', interactive=False)
    )
    with django_db_blocker.unblock():
        call_command('loaddata', 'test_dump.json')
        self = request.cls
        self.i = Institution.objects.get(name='ENS')
        self.d = Department.objects.get(name='Chemistry dept')
        self.di = Department.objects.get(name='Comp sci dept')

        self.r1 = get_researcher_by_name('Isabelle', 'Aujard')
        self.r2 = get_researcher_by_name('Ludovic', 'Jullien')
        self.r3 = get_researcher_by_name('Antoine', 'Amarilli')
        self.r4 = get_researcher_by_name('Antonin', 'Delpeuch')
        self.r5 = get_researcher_by_name('Terence', 'Tao')
        self.hal = OaiSource.objects.get(identifier='hal')
        self.arxiv = OaiSource.objects.get(identifier='arxiv')
        self.lncs = Journal.objects.get(issn='0302-9743')
        self.acm = Journal.objects.get(issn='1529-3785').publisher
    rebuild_index()
    request.addfinalizer(rebuild_index)


@pytest.fixture(scope='function')
def rebuild_index(request):
    rebuild_index = (
        lambda: call_command('rebuild_index', interactive=False)
    )
    rebuild_index()
    request.addfinalizer(rebuild_index)
