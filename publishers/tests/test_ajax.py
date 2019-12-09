import pytest

from django.contrib.auth.models import User

from dissemin.celery import app as celery_app

from papers.models import Paper
from papers.tests.test_ajax import JsonRenderingTest
from publishers.tests.test_romeo import RomeoAPIStub

@pytest.mark.usefixtures('mock_doi')
class PublisherAjaxTest(JsonRenderingTest):

    @classmethod
    def setUpClass(cls):
        super(PublisherAjaxTest, cls).setUpClass()
        u = User.objects.create_user('patrick', 'pat@mat.io', 'yo')
        u.is_superuser = True
        u.save()
        cls.romeo_api = RomeoAPIStub()
        issn = '1063-6706'
        cls.romeo_api.fetch_journal({'issn':issn})

    def setUp(self):
        super(PublisherAjaxTest, self).setUp()
        self.papers = list(map(Paper.create_by_doi,
                        ['10.1109/TFUZZ.2018.2852307', '10.1109/TFUZZ.2018.2857720']))
        self.publisher = self.papers[0].publications[0].publisher
        self.assertEqual(self.publisher, self.papers[1].publications[0].publisher)
        celery_app.conf.task_always_eager = True # run all tasks synchronously

    def test_logged_out(self):
        self.client.logout()
        req = self.postPage('ajax-changePublisherStatus',
                            postargs={'pk': self.publisher.pk, 'status': 'OA'})
        self.assertEqual(req.status_code, 302)

    def test_change_publisher_status(self):
        self.client.login(username='patrick', password='yo')
        self.assertEqual('OK', self.publisher.oa_status)
        p = self.postPage('ajax-changePublisherStatus',
                          postargs={'pk': self.publisher.pk,
                                    'status': 'OA'})
        self.assertEqual(p.status_code, 200)
        papers = [Paper.objects.get(pk=paper.pk) for paper in self.papers]
        self.assertTrue(all([paper.oa_status == 'OA' for paper in papers]))
