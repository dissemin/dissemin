# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import pytest
import django.test
from backend.oadoi import OadoiAPI
from papers.models import Paper

@pytest.mark.usefixtures("load_test_data")
class OadoiAPITest(django.test.TestCase):
    
    def test_ingest_dump(self):
        doi = '10.1080/21645515.2017.1330236'
        p = Paper.create_by_doi(doi)
        self.assertEqual(p.pdf_url, None)
        Paper.create_by_doi(doi)

        # then load an OAdoi dump
        oadoi = OadoiAPI()
        oadoi.load_dump('devutils/sample_unpaywall_snapshot.jsonl.gz')

        # the paper is now OA, yay!
        p = Paper.get_by_doi(doi)
        self.assertEqual(p.pdf_url, 'http://europepmc.org/articles/pmc5718814?pdf=render')
