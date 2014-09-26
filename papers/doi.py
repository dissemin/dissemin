# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
import re

# DOIs have very few limitations on what can appear in them
# see the standards
# hence a quite permissive regexp, as we use it in a controlled
# environment: fields of a metadata record and not plain text

doi_re = re.compile(r'(?i) *(?:DOI *[:=])? *(?:http://dx\.doi\.org/)?([^ ]+/[^ ]+) *')

# Supported formats
#
# 'http://dx.doi.org/10.1145/1721837.1721839'
# '10.1145/1721837.1721839'
# 'DOI: 10.1145/1721837.1721839'
#
# These are all converted to
# '10.1145/1721837.1721839'
def to_doi(candidate):
    """ Convert a representation of a DOI to its normal form. """
    m = doi_re.match(candidate)
    if m:
        return m.groups()[0]
    else:
        return None

