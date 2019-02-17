# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

# This is inspired from django-allauth's ProviderRegistry



import re

from django.conf import settings

try:
    import importlib
except ImportError:
    from django.utils import importlib


protocol_module_re = re.compile(r'deposit.\w+')


class ProtocolRegistry(object):

    def __init__(self):
        self.dct = {}
        self.loaded = False

    def get(self, *args, **kwargs):
        self.load()
        return self.dct.get(*args, **kwargs)

    def register(self, cls):
        self.dct[cls.__name__] = cls

    def load(self):
        if not self.loaded:
            for app in settings.INSTALLED_APPS:
                if protocol_module_re.match(app):
                    try:
                        importlib.import_module(app+'.protocol')
                    except ImportError as e:
                        print("ImportError in "+app+'.protocol')
                        print(e)
        self.loaded = True

protocol_registry = ProtocolRegistry()
