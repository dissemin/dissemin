from unittest import TestCase
from papers.fingerprint import create_paper_plain_fingerprint

class FingerprintTest(TestCase):
    def test_plain_fingerprint(self):
        self.assertEqual(create_paper_plain_fingerprint(' It  cleans whitespace And Case\\n',[('John','Doe')], 2015),
                         'it-cleans-whitespace-and-case/doe')
        self.assertEqual(create_paper_plain_fingerprint('HTML tags are <emph>removed</emph>',[('John','Doe')], 2015),
                         'html-tags-are-removed/doe')
        self.assertEqual(create_paper_plain_fingerprint('Les accents sont supprimés', [('John','Doe')],2015),
                         'les-accents-sont-supprimes/doe')
        self.assertEqual(create_paper_plain_fingerprint('Long titles are unambiguous enough to be unique by themselves, no need for authors', [('John','Doe')], 2015),
                         'long-titles-are-unambiguous-enough-to-be-unique-by-themselves-no-need-for-authors')
        self.assertEqual(create_paper_plain_fingerprint('Ambiguity', [('John','Doe')], 2014),
                         'ambiguity-2014/doe')