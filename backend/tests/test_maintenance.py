import pytest

from django.test import TestCase

from backend.maintenance import update_paper_statuses, unmerge_paper_by_dois
from papers.models import OaiRecord
from papers.models import Paper

@pytest.mark.usefixtures("load_test_data")
class MaintenanceTest(TestCase):

    @pytest.mark.usefixtures('mock_doi')
    def test_name_initial(self):
        n = self.r2.name
        p = Paper.create_by_doi("10.1002/ange.19941062339")
        n1 = p.authors[0].name
        self.assertEqual((n1.first, n1.last), (n.first, n.last))

    @pytest.mark.usefixtures('mock_doi')
    def test_update_paper_statuses(self):
        p = Paper.create_by_doi('10.1016/j.bmc.2005.06.035')
        self.assertEqual(p.pdf_url, None)
        pdf_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        OaiRecord.new(source=self.arxiv,
                      identifier='oai:arXiv.org:aunrisste',
                      about=p,
                      splash_url='http://www.perdu.com/',
                      pdf_url=pdf_url)
        update_paper_statuses()
        self.assertEqual(Paper.objects.get(pk=p.pk).pdf_url, pdf_url)

    @pytest.mark.usefixtures('mock_doi')
    def test_unmerge_paper(self):
        # First we merge two unrelated papers
        p1 = Paper.create_by_doi("10.1016/j.bmc.2005.06.035")
        title1 = p1.title
        p2 = Paper.create_by_doi("10.1016/j.ijar.2017.06.011")
        title2 = p2.title
        p1.merge(p2)
        # Then we unmerge them
        unmerge_paper_by_dois(p1)
        # We have two new papers!
        p3 = Paper.get_by_doi("10.1016/j.bmc.2005.06.035")
        self.assertTrue(p3.id != p1.id)
        self.assertEqual(p3.title, title1)
        p4 = Paper.get_by_doi("10.1016/j.ijar.2017.06.011")
        self.assertTrue(p4.id != p1.id)
        self.assertTrue(p4.id != p3.id)
        self.assertEqual(p4.title, title2)
