import pytest
from django.test import TestCase
from backend.crossref import CrossRefAPI
from backend.orcid import OrcidPaperSource
from backend.maintenance import update_paper_statuses, unmerge_paper_by_dois,\
    unmerge_orcid_nones
from papers.models import OaiRecord
from papers.models import Paper
from papers.models import Researcher
from unittest.mock import patch
from papers.tests.test_orcid import OrcidProfileStub

@pytest.mark.usefixtures("load_test_data")
class MaintenanceTest(TestCase):

    @classmethod
    def setUpClass(self):
        super(MaintenanceTest, self).setUpClass()
        self.cr_api = CrossRefAPI()

    def test_name_initial(self):
        n = self.r2.name
        p = Paper.create_by_doi("10.1002/ange.19941062339")
        n1 = p.authors[0].name
        self.assertEqual((n1.first, n1.last), (n.first, n.last))

    def test_update_paper_statuses(self):
        p = self.cr_api.create_paper_by_doi("10.1016/j.bmc.2005.06.035")
        p = Paper.from_bare(p)
        self.assertEqual(p.pdf_url, None)
        pdf_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        OaiRecord.new(source=self.arxiv,
                      identifier='oai:arXiv.org:aunrisste',
                      about=p,
                      splash_url='http://www.perdu.com/',
                      pdf_url=pdf_url)
        update_paper_statuses()
        self.assertEqual(Paper.objects.get(pk=p.pk).pdf_url, pdf_url)

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

    def test_unmerge_orcid_nones(self):
        # First, fetch a few DOIs
        dois = [
            "10.1075/aicr.90.09ngo",
            "10.1075/aicr.90.04wad",
        ]
        for doi in dois:
            Paper.create_by_doi(doi)

        # Then, fetch an ORCID profile with a buggy version of the ORCID interface, which incorrectly merges papers together
        with patch.object(OrcidPaperSource, '_oai_id_for_doi') as mock_identifier:
            mock_identifier.return_value = "https://pub.orcid.org/v2.1/0000-0002-1909-134X/work/None"
            profile = OrcidProfileStub('0000-0002-1909-134X', instance='orcid.org')
            trung = Researcher.get_or_create_by_orcid('0000-0002-1909-134X', profile=profile)
            OrcidPaperSource().fetch_and_save(trung, profile=profile)

        # The two papers are incorrectly merged!
        papers = [Paper.get_by_doi(doi) for doi in dois]
        self.assertEqual(papers[0], papers[1])

        # We unmerge them
        unmerge_orcid_nones()

        # The two papers are now distinct
        papers = [Paper.get_by_doi(doi) for doi in dois]
        self.assertTrue(papers[0] != papers[1])


