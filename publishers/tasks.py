'''
Created on 21 févr. 2019

@author: antonin
'''

from backend.utils import run_only_once
from celery import shared_task
from publishers.models import Publisher
from publishers.models import Journal
from statistics.models import AccessStatistics
from publishers.romeo import RomeoAPI

@shared_task(name='fetch_updates_from_romeo')
@run_only_once('fetch_updates_from_romeo', timeout=2*3600)
def fetch_updates_from_romeo():
    RomeoAPI().fetch_updates()

@shared_task(name='change_publisher_oa_status')
def change_publisher_oa_status(pk, status):
    publisher = Publisher.objects.get(pk=pk)
    publisher.change_oa_status(status)
    publisher.update_stats()

@shared_task(name='update_journal_stats')
@run_only_once('refresh_journal_stats', timeout=10*60)
def update_journal_stats():
    """
    Updates statistics for journals (only visible to admins, so
    not too frequently please)
    """
    AccessStatistics.update_all_stats(Journal)
