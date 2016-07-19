# -*- encoding: utf-8 -*-
from __future__ import unicode_literals


class AppConfig(django.apps.AppConfig):

    def ready(self):
        from .protocol import ZenodoProtocol
        from deposit.registry import protocol_registry
        protocol_registry.register(ZenodoProtocol)
