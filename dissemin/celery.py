import os
import logging

from celery import Celery

logger = logging.getLogger('dissemin.' + __name__)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dissemin.settings')

app = Celery('dissemin')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    logger.debug('Request: {0!r}'.format(self.request))
