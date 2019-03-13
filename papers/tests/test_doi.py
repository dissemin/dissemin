
from unittest import TestCase
from papers.doi import to_doi
from papers.doi import doi_to_url

class DoiTest(TestCase):
    def test_to_doi(self):
         self.assertEqual(to_doi('https://doi.org/10.1145/1721837.1721839'),
                          '10.1145/1721837.1721839')
         self.assertEqual(to_doi('https://doi.org/10.1145/1721837.1721839'),
                          '10.1145/1721837.1721839')
         self.assertEqual(to_doi('10.1145/1721837.1721839'),
                          '10.1145/1721837.1721839')
         self.assertEqual(to_doi('DOI: 10.1145/1721837.1721839'),
                          '10.1145/1721837.1721839')
         self.assertEqual(to_doi('info:eu-repo/semantics/altIdentifier/doi/10.1145/1721837.1721839'),
                          '10.1145/1721837.1721839')
         self.assertEqual(to_doi('10.1093/jhmas/XXXI.4.480'),
                          '10.1093/jhmas/xxxi.4.480')
    
    def test_doi_to_url(self):
         self.assertEqual(doi_to_url('10.1093/jhmas/xxxi.4.480'),
                          'https://doi.org/10.1093/jhmas/xxxi.4.480')