# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from backend.tests import PrefilledTest
from backend.oadoi import OadoiAPI
from papers.models import Paper

class OadoiAPITest(PrefilledTest):
    def test_ingest_dump(self):
        doi1 = '10.1016/j.reval.2012.02.143'
        p = Paper.create_by_doi(doi1)
        self.assertEqual(p.pdf_url, None)
        Paper.create_by_doi(doi2)

        # then load an OAdoi dump
        oadoi = OadoiAPI()
        oadoi.load_dump('devutils/sample_oadoi_dump.csv.gz')

        # the paper is now OA, yay!
        p = Paper.get_by_doi(doi)
        self.assertEqual(p.pdf_url, 'http://prodinra.inra.fr/ft/CC06E77F-B3EE-4BD2-890D-067243B8ACAF')
