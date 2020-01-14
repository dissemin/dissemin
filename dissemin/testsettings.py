from dissemin.settings import *
from dissemin.celery import app

DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': lambda r: False}
app.conf.task_always_eager = True

# We delete the logger 'dissemin', so that it goes to root logger and gets catched by pytest caplog fixture
try:
    del LOGGING['loggers']['dissemin']
except KeyError:
    pass
