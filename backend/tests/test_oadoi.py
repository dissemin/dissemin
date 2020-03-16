import os
import pytest

import django.test

from backend.oadoi import OadoiAPI
from papers.models import Paper

@pytest.mark.usefixtures("load_test_data")
class OadoiAPITest(django.test.TestCase):

    @classmethod
    def setUpClass(cls):
        super(OadoiAPITest, cls).setUpClass()
        cls.testdir = os.path.dirname(os.path.abspath(__file__))

    @pytest.mark.usefixtures('mock_doi')
    def test_ingest_dump(self):
        doi = '10.1080/21645515.2017.1330236'
        p = Paper.create_by_doi(doi)
        self.assertEqual(p.pdf_url, None)
        Paper.create_by_doi(doi)

        # then load an OAdoi dump
        oadoi = OadoiAPI()
        oadoi.load_dump(os.path.join(self.testdir, 'data/sample_unpaywall_snapshot.jsonl.gz'))

        # the paper is now OA, yay!
        p = Paper.get_by_doi(doi)
        self.assertEqual(p.pdf_url, 'http://europepmc.org/articles/pmc5718814?pdf=render')
