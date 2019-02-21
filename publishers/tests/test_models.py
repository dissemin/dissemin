'''
Created on 21 févr. 2019

@author: antonin
'''

from publishers.models import Journal
from django.test import TestCase
from publishers.tests.test_romeo import RomeoAPIStub

class JournalTest(TestCase):
    
    def setUp(self):
        super(JournalTest, self).setUp()
        self.publisher = RomeoAPIStub().fetch_publisher('Harvard University Press')
    
    def test_find(self):
        j1 = Journal(title='Journal of Synthetic Disillusion',
                     issn=None,
                     essn='1234-0707',
                     publisher=self.publisher)
        j1.save()
        j2 = Journal(title='Slackline Review',
                     issn='4353-2894',
                     essn=None,
                     publisher=self.publisher)
        j2.save()

        self.assertEqual(Journal.find(title='Slackline Review'), j2)
        self.assertEqual(Journal.find(title='slackline review'), j2)
        # We look for ISSN and ESSN in both fields, because they could easily be swapped!
        self.assertEqual(Journal.find(issn='1234-0707'), j1)
        self.assertEqual(Journal.find(essn='1234-0707'), j1)
        self.assertEqual(Journal.find(issn='4353-2894'), j2)
        self.assertEqual(Journal.find(essn='4353-2894'), j2)
        self.assertEqual(Journal.find(title='nonsense'), None)