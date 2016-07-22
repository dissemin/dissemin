# -*- encoding: utf-8 -*-
from __future__ import unicode_literals


class AppConfig(django.apps.AppConfig):

    def ready(self):
        from deposit.zenodo.providers import *
