"""
Travis specific settings for tests
"""

from .common import *

# Patch urllib3 because the default SSL module on Travis sucks
import urllib3.contrib.pyopenssl
urllib3.contrib.pyopenssl.inject_into_urllib3()
