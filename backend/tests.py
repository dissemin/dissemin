# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

from __future__ import unicode_literals

import unittest
from django.test import TestCase
from backend.core import *
from backend.crossref import *
from backend.romeo import *
from backend.orcid import *
from backend.oai import *
from backend.tasks import *
from backend.maintenance import *
from papers.models import *
from papers.errors import *
from publishers.models import *

import datetime

from lxml import etree

# SHERPA/RoMEO interface
class RomeoTest(TestCase):
    def test_perform_query(self):
        self.assertIsInstance(perform_romeo_query({'issn':'0022-328X'}), etree._ElementTree)
        self.assertIsInstance(perform_romeo_query({'jtitle':'Physical Review E'}), etree._ElementTree)

    def test_fetch_journal(self):
        terms = {'issn':'0022-328X'}
        orig_terms = terms.copy()
        self.assertIsInstance(fetch_journal(terms), Journal)
        self.assertEqual(terms, orig_terms)
        journal = find_journal_in_model(terms)
        self.assertIsInstance(journal, Journal)
        self.assertEqual(journal.issn, terms['issn'])

    def test_unicode(self):
        terms = {'issn':'0375-0906'}
        journal = fetch_journal(terms)
        self.assertEqual(journal.title, 'Revista de Gastroenterología de México')
        self.assertEqual(journal.publisher.name, 'Elsevier España')

    def test_openaccess(self):
        self.assertEqual(fetch_journal({'issn':'1471-2105'}).publisher.oa_status, 'OA')
        self.assertEqual(fetch_journal({'issn':'1951-6169'}).publisher.oa_status, 'OA')

    def test_closed(self):
        self.assertEqual(fetch_journal({'issn':'0732-183X'}).publisher.oa_status, 'NOK')

    def test_open(self):
        self.assertEqual(fetch_journal({'issn':'1631-073X'}).publisher.oa_status, 'OK')
        self.assertEqual(fetch_journal({'issn':'0099-2240'}).publisher.oa_status, 'OK')
        self.assertEqual(fetch_journal({'issn':'0036-8075'}).publisher.oa_status, 'OK')

# Generic test case that requires some example DB
class PrefilledTest(TestCase):
    @classmethod
    def setUpClass(self):
        if self is PrefilledTest:
            raise unittest.SkipTest("Base test")
        self.i, _ = Institution.objects.get_or_create(name='ENS')
        self.d, _ = Department.objects.get_or_create(name='Chemistry dept', institution=self.i)
        self.di, _ = Department.objects.get_or_create(name='Comp sci dept', institution=self.i)
        self.r1 = Researcher.get_or_create_by_name('Isabelle', 'Aujard', department=self.d)
        self.r2 = Researcher.get_or_create_by_name('Ludovic', 'Jullien', department=self.d)
        self.r3 = Researcher.get_or_create_by_name('Antoine', 'Amarilli', department=self.di)
        self.r4 = Researcher.get_or_create_by_name('Antonin', 'Delpeuch', department=self.di, orcid=
            '0000-0002-8612-8827')
        self.r5 = Researcher.get_or_create_by_name('Terence', 'Tao')
        self.hal, _ = OaiSource.objects.get_or_create(identifier='hal',
                name='HAL',
                default_pubtype='preprint')
        self.arxiv, _ = OaiSource.objects.get_or_create(identifier='arxiv',
                name='arXiv',
                default_pubtype='preprint')

    @classmethod
    def tearDownClass(self):
        name_lookup_cache.prune()

    def tearDown(self):
        name_lookup_cache.prune()

def check_paper(asserter, paper):
    """
    All sorts of tests to ensure a paper is well-behaved
    """
    # All authors should have valid names
    paper.check_authors()
    # Visible papers should have at least one source
    if paper.visibility == 'VISIBLE': 
        asserter.assertTrue(paper.oairecord_set.count()+paper.publication_set.count() > 0)

# Generic test series for a PaperSource instance
class PaperSourceTest(PrefilledTest):
    @classmethod
    def setUpClass(self):
        super(PaperSourceTest, self).setUpClass()
        if self is PaperSourceTest:
            raise unittest.SkipTest("Base test")
        self.ccf = get_ccf()
        self.source = None
        self.researcher = self.r4

    def test_fetch(self):
        papers = list(self.source.fetch_papers(self.researcher))
        for p in papers:
            check_paper(self, p)
        self.assertTrue(len(papers) > 1)
        self.check_papers(papers)

    def check_papers(self, papers):
        """
        Method that subclasses can reimplement to check the papers
        downloaded in test_fetch.
        """
        pass

    def test_empty(self):
        emptyres = Researcher.get_or_create_by_name('Anrscuienrsc','Lecsrcudresies')
        papers = list(self.source.fetch_papers(emptyres))
        self.assertEqual(papers, [])

# Test that the CORE interface works
class CoreTest(PaperSourceTest):
    @classmethod
    def setUpClass(self):
        super(CoreTest, self).setUpClass()
        self.source = CorePaperSource(self.ccf)
        self.researcher = self.r5

    def test_query(self):
        self.assertIsInstance(
                query_core('/articles/get/19822106', {}),
                dict)
        self.assertIsInstance(
                query_core('/search/Geoffrey+Bodenhausen', {}),
                dict)

    def test_search(self):
        num_results = 10
        record_list = list(search_single_query('authorsString:(Antoine Amarilli)', num_results))
        self.assertEqual(len(record_list), num_results)

    def test_single_query(self):
        num_results = 210 # so that multiple batches are done
        records = list(fetch_paper_metadata_by_core_ids(search_single_query('homotopy', num_results)))
        self.assertTrue(len(records) < num_results)
        self.assertTrue(len(records) > 1)

class CrossRefOaiTest(PaperSourceTest):
    """
    Test for the CrossRef interface with OAI availability fetching
    """
    @classmethod
    def setUpClass(self):
        super(CrossRefOaiTest, self).setUpClass()
        self.oaisource = OaiPaperSource(self.ccf) 
        self.source = CrossRefPaperSource(self.ccf, oai=self.oaisource)

class CrossRefIntegrationTest(PaperSourceTest):
    @classmethod
    def setUpClass(self):
        super(CrossRefIntegrationTest, self).setUpClass()
        self.source = CrossRefPaperSource(self.ccf)

    def check_papers(self, papers):
        # Check affiliations are kept
        p = Publication.objects.get(doi='10.4204/eptcs.172.16')
        self.assertEqual(p.paper.author_set.all()[0].affiliation, 'École Normale Supérieure, Paris')
        # Check that each paper has a publication
        for p in papers:
            self.assertTrue(len(p.publication_set.all()) > 0)

    def check_previously_present_papers_are_attributed(self):
        # Fetch papers from a researcher
        r = Researcher.get_or_create_by_name('Laurent','Bienvenu')
        self.source.fetch(r, incremental=True)

        # Now fetch a coauthor of him
        r2 = Researcher.get_or_create_by_orcid('0000-0003-1698-5150')
        self.source.fetch(r2, incremental=True)

        # This paper should be attributed
        p = Paper.objects.get(publication__doi='10.1016/j.jcss.2015.04.004')
        self.assertEqual(p.sorted_authors[3].researcher, r2)


class CrossRefUnitTest(unittest.TestCase):
    def test_fetch_single_doi(self):
        doi = '10.5380/dp.v1i1.1922'
        metadata = fetch_metadata_by_DOI(doi)
        self.assertEqual(metadata,
                {'publisher': 'Universidade Federal do Parana',
                 'DOI': '10.5380/dp.v1i1.1922',
                 'subtitle': [],
                 'author': [{'given': 'Frederic', 'family': 'Worms'}],
                 'URL': 'http://dx.doi.org/10.5380/dp.v1i1.1922',
                 'issued': {'date-parts': [[2005, 3, 18]]},
                 'reference-count': 0,
                 'title': 'A concep\xe7\xe3o bergsoniana do tempo',
                 'volume': '1',
                 'source': 'CrossRef',
                 'prefix': 'http://id.crossref.org/prefix/10.5380',
                 'score': 1.0,
                 'deposited': {'timestamp': 1421107200000, 'date-parts': [[2015, 1, 13]]},
                 'type': 'journal-article',
                 'container-title': 'DoisPontos',
                 'indexed': {'timestamp': 1421405831942, 'date-parts': [[2015, 1, 16]]}, 
                 'issue': '1',
                 'ISSN': ['2179-7412', '1807-3883'],
                 'member': 'http://id.crossref.org/member/3785'})

    def test_parse_crossref_date_incomplete(self):
        self.assertEqual(
                parse_crossref_date({'date-parts': [[2015,07,06]]}),
                datetime.date(year=2015,month=07,day=06))
        self.assertEqual(
                parse_crossref_date({'date-parts': [[2015,07]]}),
                datetime.date(year=2015,month=07,day=01))
        self.assertEqual(
                parse_crossref_date({'date-parts': [[2015]]}),
                datetime.date(year=2015,month=01,day=01))

    def test_parse_crossref_date_raw(self):
        self.assertEqual(
                parse_crossref_date({'raw': '2015'}),
                datetime.date(year=2015,month=01,day=01))
        self.assertEqual(
                parse_crossref_date({'raw': '2015-07'}),
                datetime.date(year=2015,month=07,day=01))
        self.assertEqual(
                parse_crossref_date({'raw': '2015-07-06'}),
                datetime.date(year=2015,month=07,day=06))

    def test_get_publication_date(self):
        self.assertEqual(
                get_publication_date(fetch_metadata_by_DOI('10.5281/zenodo.18898')),
                datetime.date(year=2015,month=01,day=01))
        self.assertEqual(
                get_publication_date(fetch_metadata_by_DOI('10.5380/dp.v1i1.1919')),
                datetime.date(year=2005,month=03,day=18))

    def test_batch_queries(self):
        dois = [
            '10.1007/978-3-540-46375-7_2',
            '10.1007/978-3-540-46375-7_9',
            '10.2307/2540916',
            '10.1016/s1169-8330(00)80059-9',
            '10.1017/s0022112009008003',
            '10.1051/proc/2011014',
            '10.1016/0169-5983(88)90079-2',
            '10.1080/14685240600601061',
            '10.1103/physreve.79.026303',
            '10.1103/physreve.66.046307',
            '10.1103/physrevlett.95.244502',
            '10.1017/s0022112089002351',
            '10.1063/1.4738850',
            '10.1103/physrevlett.87.054501',
            '10.1080/14685248.2012.711476',
            '10.1007/978-94-011-4177-2_12',
            '10.1007/978-1-4615-4697-9_2',
            '10.1007/978-1-4612-0137-3_7',
            '10.1007/978-1-4020-6472-2_35']
        incremental = list(fetch_dois_incrementally(dois))
        self.assertEqual(len(incremental), len(dois))
        if DOI_PROXY_SUPPORTS_BATCH:
            batch = fetch_dois_by_batch(dois)
            self.assertEqual([item['DOI'] for item in incremental],
                             [item['DOI'] for item in batch])

    def test_dirty_batches(self):
        with self.assertRaises(MetadataSourceException):
            fetch_dois_by_batch(['aunirestauniecb898989']) # definitely not a DOI

        dois = ['10.5281/anuirsetacesecesrbl'] # probably not a DOI
        results = fetch_dois_by_batch(dois)
        self.assertTrue(all([item is None for item in results]))

    def test_mixed_queries(self):
        dois = [
            '10.1016/0169-5983(88)90079-2', # CrossRef DOI
            '10.5281/zenodo.12826', # DataCite DOI
            ]
        results = fetch_dois_by_batch(dois)
        self.assertEqual([item['DOI'] for item in results], dois)

    def test_convert_to_name_pair(self):
        self.assertEqual(
                convert_to_name_pair({'family':'Farge','given':'Marie'}),
                ('Marie','Farge'))
        self.assertEqual(
                convert_to_name_pair({'literal':'Marie Farge'}),
                ('Marie','Farge'))
        self.assertEqual(
                convert_to_name_pair({'literal':'Farge, Marie'}),
                ('Marie','Farge'))
        self.assertEqual(
                convert_to_name_pair({'family':'Arvind'}),
                ('','Arvind'))


# Test that the proaixy interface works
class OaiTest(PaperSourceTest):
    @classmethod
    def setUpClass(self):
        super(OaiTest, self).setUpClass()
        self.source = OaiPaperSource(self.ccf)

    def test_signature(self):
        for idx, p in enumerate(self.source.fetch_records_for_name(self.r3.name, signature=True)):
            if idx > 10:
                break

    def test_full_name(self):
        for idx, p in enumerate(self.source.fetch_records_for_name(self.r3.name, signature=False)):
            if idx > 10:
                break

class OrcidUnitTest(unittest.TestCase):
    def test_affiliate_author(self):
        self.assertEqual(
                affiliate_author_with_orcid(
                ('Jordi','Cortadella'),
                '0000-0001-8114-250X',
                [('N.','Nikitin'), ('J.','De San Pedro'),('J.','Carmona'), ('J.','Cortadella')]),
                [None,None,None,'0000-0001-8114-250X'])
        self.assertEqual(
                affiliate_author_with_orcid(
                ('Antonin','Delpeuch'),
                '0000-0002-8612-8827',
                [('Antonin','Delpeuch'),('Anne','Preller')]),
                ['0000-0002-8612-8827',None])

class OrcidIntegrationTest(PaperSourceTest):
    @classmethod
    def setUpClass(self):
        super(OrcidIntegrationTest, self).setUpClass()
        self.source = OrcidPaperSource(self.ccf)

    def check_papers(self, papers):
        p = Paper.objects.get(title='From Natural Language to RDF Graphs with Pregroups')
        p.check_authors()
        author = p.author_set.get(position=0)
        self.assertEqual(author.affiliation, self.r4.orcid)
        p = Paper.objects.get(title='Complexity of Grammar Induction for Quantum Types')
        p.check_authors()
        author = p.author_set.get(position=0)
        self.assertEqual(author.affiliation, self.r4.orcid)


class PaperMethodsTest(PrefilledTest):
    @classmethod
    def setUpClass(self):
        if self is PaperMethodsTest:
            raise unittest.SkipTest("Base test")
        self.ccf = get_ccf()

    def test_update_author_names(self):
        for old_author_names, new_author_names, final in [
                ([('G.','Bodenhausen')],
                 [('Geoffrey','Bodenhausen')],
                 [('Geoffrey','Bodenhausen')]),
                ([('L. F.','Jullien'),('A.','Amarilli')],
                 [('Ludovic','Jullien'),('R.','Pérand'),('Antoine','Amarilli')],
                 [('Ludovic F.','Jullien'),('R.','Pérand'),('Antoine','Amarilli')]),
                ]:
            paper = self.ccf.get_or_create_paper('This is a test paper',
                    map(Name.lookup_name, old_author_names), datetime.date(year=2015,month=04,day=05))
            self.ccf.commitThemAll()
            paper.update_author_names(new_author_names)
            self.assertEqual(paper.bare_author_names(), final)

    def test_multiple_get_or_create(self):
        date = datetime.date(year=2003,month=4,day=9)
        paper = self.ccf.get_or_create_paper('Beta-rays in black pudding',
                map(Name.lookup_name, [('F.','Rodrigo'),('A.','Johnson'),('Pete','Blunsom')]),
                date)

        paper2 = self.ccf.get_or_create_paper('Beta-rays in black pudding',
                map(Name.lookup_name, [('Frank','Rodrigo'),('A. L.','Johnson'),('P.','Blunsom')]),
                date)

        self.assertEqual(paper.pk, paper2.pk)
        self.assertEqual(paper.bare_author_names(), [('Frank','Rodrigo'),('A. L.','Johnson'),
            ('Pete','Blunsom')])


class MaintenanceTest(PrefilledTest):
    @classmethod
    def setUpClass(self):
        super(MaintenanceTest, self).setUpClass()
        self.ccf = get_ccf()
        crps = CrossRefPaperSource(self.ccf)
        crps.fetch(self.r2)
        consolidate_paper(Publication.objects.get(doi='10.1021/cb400178m').paper_id)

    def test_create_publisher_aliases(self):
        create_publisher_aliases()

    def test_journal_to_publisher(self):
        journal_to_publisher()

    def test_refetch_publishers(self):
        refetch_publishers()

    def test_refetch_containers(self):
        refetch_containers()

    def test_recompute_publisher_policies(self):
        recompute_publisher_policies()

    def test_cleanup_papers(self):
        cleanup_papers()

    def test_cleanup_researchers(self):
        cleanup_researchers()

    def test_prune_name_lookup_cache(self):
        prune_name_lookup_cache(3)
        self.assertTrue(name_lookup_cache.check())
        prune_name_lookup_cache(None)
        self.assertTrue(name_lookup_cache.check())
        self.assertEqual(len(name_lookup_cache.cnt), 0)
        self.assertEqual(len(name_lookup_cache.dct), 0)

    def test_cleanup_names(self):
        n = Name.lookup_name(('Anaruic','Leclescuantebrste'))
        n.save()
        cleanup_names()
        self.assertEqual(Name.lookup_name(('Anaruic','Leclescuantebrste')).pk, None)

    def test_name_initial(self):
        n = self.r2.name
        p = Publication.objects.get(doi="10.1002/ange.19941062339").paper
        n1 = p.author_set.get(position=0).name
        self.assertEqual(p.author_set.get(position=0).name, n)

    def test_merge_names(self):
        n = Name.lookup_name(('Isabelle','Autard'))
        n.save()
        merge_names(self.r1.name, n)
        self.assertEqual(Researcher.objects.get(pk=self.r1.pk).name, n)
        p = Publication.objects.get(doi="10.1002/anie.200800037").paper
        self.assertEqual(p.author_set.get(position=1).name, n)

    def test_update_paper_statuses(self):
        p = Publication.objects.get(doi="10.1002/anie.200800037").paper
        self.assertEqual(p.pdf_url, None)
        pdf_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        oairecord = OaiRecord.new(source=self.arxiv,
                identifier='oai:arXiv.org:aunrisste',
                about=p,
                splash_url='http://www.perdu.com/',
                pdf_url=pdf_url)
        update_paper_statuses()
        self.assertEqual(Paper.objects.get(pk=p.pk).pdf_url, pdf_url)

    def test_cleanup(self):
        oaips = OaiPaperSource(self.ccf)
        oaips.fetch(self.r3)
        cleanup_titles()
        cleanup_abstracts()


