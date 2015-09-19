# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

from __future__ import unicode_literals


class PaperSource(object):
    """
    Abstract interface for something that adds papers from some metadata source
    for a given researcher.
    """

    def __init__(self, ccf, oai=None, max_results=None):
        """
        To construct a PaperSource, a Clustering Context Factory (ccf)
        is required: this allows us to cluster incoming papers and
        assign them to researchers.

        If an OAI interface is provided, this allows us to check full
        text availability as the papers are fetched. This should be used
        for sources where full text availability is not provided in the metadata
        (CrossRef, ORCID).

        Subclasses can reimplement the constructor to get parameters for the source.
        Do not forget to call this base constructor though.

        :param max_results: maximum number of papers to retrieve for each researcher.
        """
        self.ccf = ccf
        self.oai = oai
        self.max_results = None

    def fetch_papers(self, researcher):
        """
        This function is the one subclasses should reimplement.
        Given a researcher, it should yield all the papers it can
        fetch from the source.
        """
        raise NotImplemented("fetch_papers should be implemented by the subclass")

    def fetch(self, researcher, incremental=False):
        """
        This function is the one users should use to fetch papers.

        :param incremental: When set to true, papers are clustered
            and commited one after the other. This is useful when
            papers are fetched on the fly for an user.
        """
        count = 0
        for p in self.fetch_papers(researcher):
            count += 1
            print "--- Reseracher task: "+str(researcher.current_task)
            if self.oai:
                p = self.oai.fetch_accessibility(p)
            if incremental:
                self.ccf.load(researcher)
                self.ccf.cc[researcher.pk].commit()
            if self.max_results is not None and count >= self.max_results:
                break


