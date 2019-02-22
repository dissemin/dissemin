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
        
    def test_merge(self):
        # Temporarily fake the romeo_id of our publisher
        correct_romeo_id = self.publisher.romeo_id
        self.publisher.romeo_id = '12345'
        self.publisher.save()
        
        # Fetch a journal from the publisher: this creates a duplicate publisher
        journal = RomeoAPIStub().fetch_journal({'issn':'0073-0688'})
        new_publisher = journal.publisher
        self.assertNotEqual(self.publisher.id, new_publisher.id)
        
        # Restore the romeo_id of our original publisher
        self.publisher.romeo_id = correct_romeo_id
        self.publisher.save()
        
        # Merge 
        self.publisher.merge(new_publisher)
        
        # Check that the journal was redirected
        journal = Journal.objects.get(id=journal.id)
        self.assertEqual(journal.publisher_id, self.publisher.id)
        