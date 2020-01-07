# -*- encoding: utf-8 -*-


import pytest
import unittest

from backend.citeproc import CrossRef
from backend.orcid import affiliate_author_with_orcid
from backend.orcid import OrcidPaperSource
from papers.models import Paper
from papers.models import Researcher
from papers.tests.test_orcid import OrcidProfileStub


class TestOrcid():
    """
    Class to group some ORCID tests
    """

    @pytest.mark.usefixtures('mock_doi')
    def test_enhance_paper(self, researcher_lesot):
        """
        Enhances paper with ORCID data
        """
        doi = '10.1016/j.ijar.2017.06.011'
        p = Paper.create_by_doi(doi)
        o = OrcidPaperSource()
        ref_name = (researcher_lesot.name.first, researcher_lesot.name.last)
        p = o._enhance_paper(p, ref_name, researcher_lesot.orcid)
        # Lesot is now a researcher of the paper
        assert p.authors_list[1]['researcher_id'] == researcher_lesot.pk
        # There must be a second OaiRecord
        p.cache_oairecords() # Cache is not up to date
        assert len(p.oairecords) == 2

    @pytest.mark.usefixtures('mock_doi')
    def test_enhance_paper_orcid_oai_exists(self, researcher_lesot):
        """
        If source exists, nothing must happen
        """
        doi = '10.1016/j.ijar.2017.06.011'
        p = Paper.create_by_doi(doi)
        o = OrcidPaperSource()
        ref_name = (researcher_lesot.name.first, researcher_lesot.name.last)
        p = o._enhance_paper(p, ref_name, researcher_lesot.orcid)
        # Lesot is now a researcher of the paper
        assert p.authors_list[1]['researcher_id'] == researcher_lesot.pk
        # There must be a second OaiRecord
        p.cache_oairecords() # Cache is not up to date
        assert len(p.oairecords) == 2


    @pytest.mark.usefixtures('mock_crossref')
    def test_fetch_metadata_from_dois(self, researcher_lesot):
        """
        Fetch metadata from doi
        """
        dois = ['10.1016/j.ijar.2017.06.011']
        o = OrcidPaperSource()
        ref_name = (researcher_lesot.name.first, researcher_lesot.name.last)
        papers = list(o.fetch_metadata_from_dois(ref_name, researcher_lesot.orcid, dois))
        assert len(papers) == 1
        p = papers[0]
        # Lesot is now a researcher of the paper
        assert p.authors_list[1]['researcher_id'] == researcher_lesot.pk
        # There must be a second OaiRecord
        p.cache_oairecords() # Cache is not up to date
        assert len(p.oairecords) == 2

    @pytest.mark.usefixtures('mock_crossref', 'mock_doi')
    def test_fetch_metadata_from_dois_orcid_oai_exists(self, researcher_lesot):
        """
        If source exists, nothing must happen
        """
        dois = ['10.1016/j.ijar.2017.06.011']
        Paper.create_by_doi(dois[0])
        o = OrcidPaperSource()
        ref_name = (researcher_lesot.name.first, researcher_lesot.name.last)
        papers = list(o.fetch_metadata_from_dois(ref_name, researcher_lesot.orcid, dois))
        assert len(papers) == 1
        p = papers[0]
        # Lesot is now a researcher of the paper
        assert p.authors_list[1]['researcher_id'] == researcher_lesot.pk
        # There must be a second OaiRecord
        p.cache_oairecords() # Cache is not up to date
        assert len(p.oairecords) == 2

    def test_fetch_metadata_from_dois_no_paper(self, monkeypatch):
        """
        If no paper created, expect None
        """
        monkeypatch.setattr(Paper, 'create_by_doi', lambda x: None)
        monkeypatch.setattr(CrossRef, 'fetch_batch', lambda x: [None])
        o = OrcidPaperSource()
        papers = list(o.fetch_metadata_from_dois('spam', 'ham', ['any_doi']))
        assert len(papers) == 1
        assert papers[0] is None


class OrcidUnitTest(unittest.TestCase):

    def test_affiliate_author(self):
        self.assertEqual(
                affiliate_author_with_orcid(
                    ('Jordi', 'Cortadella'),
                    '0000-0001-8114-250X',
                    [('N.', 'Nikitin'), ('J.', 'De San Pedro'), ('J.', 'Carmona'), ('J.', 'Cortadella')]),
                [None, None, None, '0000-0001-8114-250X'])
        self.assertEqual(
                affiliate_author_with_orcid(
                    ('Antonin', 'Delpeuch'),
                    '0000-0002-8612-8827',
                    [('Antonin', 'Delpeuch'), ('Anne', 'Preller')]),
                ['0000-0002-8612-8827', None])

@pytest.mark.usefixtures("load_test_data")
class OrcidIntegrationTest(unittest.TestCase):

    def setUp(self):
        self.source = OrcidPaperSource()
        self.researcher = self.r4

    @pytest.mark.usefixtures('mock_crossref', 'mock_doi')
    def test_fetch_orcid_records(self):
        profile = OrcidProfileStub('0000-0002-8612-8827', instance='orcid.org')
        papers = list(self.source.fetch_orcid_records(self.researcher.orcid, profile=profile))
        self.assertTrue(len(papers) > 1)
        self.check_papers(papers)

    @pytest.mark.usefixtures('mock_doi')
    def check_papers(self, papers):
        p = Paper.objects.get(
            title='From Natural Language to RDF Graphs with Pregroups')
        p.check_authors()
        author = p.authors[0]
        self.assertEqual(author.orcid, self.r4.orcid)
        p = Paper.objects.get(
            title='Complexity of Grammar Induction for Quantum Types')
        p.check_authors()
        author = p.authors[0]
        self.assertEqual(author.orcid, self.r4.orcid)

    @pytest.mark.usefixtures('mock_crossref')
    def test_previously_present_papers_are_attributed(self):
        # Fetch papers from a researcher
        profile_pablo = OrcidProfileStub('0000-0002-6293-3231', instance='orcid.org')
        pablo = Researcher.get_or_create_by_orcid('0000-0002-6293-3231',
                profile=profile_pablo)
        self.source.fetch_and_save(pablo, profile=profile_pablo)

        p = Paper.objects.get(oairecord__doi='10.1007/978-3-642-25516-8_1')
        self.assertEqual(p.authors[2].orcid, pablo.orcid)

        # Now fetch a coauthor of him
        profile_antoine = OrcidProfileStub('0000-0002-7977-4441', instance='orcid.org')
        antoine = Researcher.get_or_create_by_orcid('0000-0002-7977-4441',
                    profile=profile_antoine)
        self.source.fetch_and_save(antoine, profile=profile_antoine)

        # This paper should be attributed to both ORCID ids
        p = Paper.objects.get(oairecord__doi='10.1007/978-3-642-25516-8_1')

        self.assertEqual(p.authors[0].orcid, antoine.orcid)
        self.assertEqual(p.authors[2].orcid, pablo.orcid)

    @pytest.mark.usefixtures('mock_crossref', 'mock_doi')
    def test_orcid_affiliation(self):
        # this used to raise an error.
        # a more focused test might be preferable (focused on the said
        # paper)
        papers = list(self.source.fetch_orcid_records('0000-0002-9658-1473',
                        OrcidProfileStub('0000-0002-9658-1473')))
        self.assertTrue(len(papers) > 30)

    @pytest.mark.skip(reason="Test does not test bibtex fallback as DOI is imported via DOI backend")
    def test_bibtex_fallback(self):
        papers = list(self.source.fetch_orcid_records('0000-0002-1900-3901',
                  profile=OrcidProfileStub('0000-0002-1900-3901')))
        titles = [paper.title for paper in papers]
        self.assertTrue('Company-Coq: Taking Proof General one step closer to a real IDE' in titles)

    @pytest.mark.usefixtures('mock_crossref', 'mock_doi')
    def test_import_with_crossref_error(self):
        profile = OrcidProfileStub('0000-0001-9232-4042', instance='orcid.org')
        stergios = Researcher.get_or_create_by_orcid('0000-0001-9232-4042',
                 profile=profile)
        self.source.fetch_and_save(stergios, profile=profile)
        p = Paper.objects.get(oairecord__doi='10.1016/j.metabol.2017.10.007')
        # crossref claims that the ORCID should be associated to author 2
        # but it should actually be associated to author 0
        self.assertEqual(p.authors[0].orcid, '0000-0001-9232-4042')
        self.assertEqual(p.authors[2].orcid, None)
        self.assertEqual(p.authors[0].researcher_id, stergios.id)
        self.assertEqual(p.authors[2].researcher_id, None)

    @pytest.mark.usefixtures('mock_crossref')
    def test_bibtex_not_ignored(self):
        profile = OrcidProfileStub('0000-0003-2888-1770', instance='orcid.org')
        adrien = Researcher.get_or_create_by_orcid('0000-0003-2888-1770', profile=profile)
        self.source.fetch_and_save(adrien, profile=profile)
        p1 = Paper.objects.get(title='A Fuzzy Take on Graded Beliefs')
        p2 = Paper.objects.get(title='Information quality and uncertainty')
        self.assertTrue(p1 != p2)
        
    @pytest.mark.usefixtures('mock_crossref')
    def test_link_existing_papers(self):
        # Fetch papers from a researcher
        profile_pablo = OrcidProfileStub('0000-0002-6293-3231', instance='orcid.org')
        pablo = Researcher.get_or_create_by_orcid('0000-0002-6293-3231',
                profile=profile_pablo)
        self.source.fetch_and_save(pablo, profile=profile_pablo)
        papers = list(pablo.papers)
        nb_papers = len(papers)
        self.assertEqual(nb_papers, 9)
        
        # Remove the researcher_ids from the papers
        for paper in papers:
            for author in paper.authors_list:
                if author.get('researcher_id') == pablo.id:
                    del author['researcher_id']
            paper.save()
        
        # Now the profile has no papers anymore    
        self.assertEqual(pablo.papers.count(), 0)
        
        # Let's fix that!
        self.source.link_existing_papers(pablo)
        
        # Now it's fine!!
        self.assertEqual(Researcher.objects.get(id=pablo.id).papers.count(), 9)
                


