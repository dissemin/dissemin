# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from backend.core import *
from backend.crossref import *
from backend.oai import *
from backend.tasks import *
from papers.models import *

# Generic test case that requires some example DB

class PrefilledTest(TestCase):
    def fillDB(self):
        self.d = Department.objects.create(name='Chemistry dept')
        self.r1 = Researcher.create_from_scratch('Isabelle', 'Aujard', self.d, None, None, None)
        self.r2 = Researcher.create_from_scratch('Ludovic', 'Jullien', self.d, None, None, None)
        self.hal = OaiSource.objects.create(identifier='hal',
                name='HAL',
                default_pubtype='preprint')

# Test that the CORE interface works
class CoreTest(PrefilledTest):
    def setUp(self):
        self.fillDB()

    def test_core_interface_works(self):
        fetch_papers_from_core_for_researcher(self.r1)

# Test that the CrossRef interface works
class CrossRefTest(PrefilledTest):
    def setUp(self):
        self.fillDB()

    def test_crossref_interface_works(self):
        fetch_dois_for_researcher(self.r1.pk)

# Test that the proaixy interface works
class ProaixyTest(PrefilledTest):
    def setUp(self):
        self.fillDB()

    def test_proaixy_interface_works(self):
        fetch_records_for_researcher(self.r1.pk)

