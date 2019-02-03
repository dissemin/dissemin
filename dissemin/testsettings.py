from dissemin.settings import *
from dissemin.celery import app

DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': lambda r: False}
app.conf.task_always_eager = True
