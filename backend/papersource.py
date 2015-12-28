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

    def fetch_bare(self, researcher):
        """
        This function returns a generator of :class:`BarePaper`s fetched for the given researcher.
        """
        for p in self.fetch_papers(researcher):
            # If an OAI source is set up to check the availability, do so
            if self.oai:
                p = self.oai.fetch_accessibility(p)
            yield p

    def fetch_and_save(self, researcher, incremental=False):
        """
        Fetch papers and save them to the database.

        :param incremental: When set to true, papers are clustered
            and commited one after the other. This is useful when
            papers are fetched on the fly for an user.
        """
        for p in self.fetch_bare(researcher):        
            # Save the paper as non-bare
            p = self.ccf.save_paper(p)

            # If clustering happens incrementally, cluster the researcher
            if incremental:
                # First, check whether this paper is associated with an ORCID id
                # for the target researcher
                if researcher.orcid:
                    matches = filter(lambda a: a.orcid == researcher.orcid, p.authors)
                    if matches:
                        self.update_empty_orcid(researcher, False)
                
                # Then, cluster the new author
                self.ccf.clusterPendingAuthorsForResearcher(researcher)
                researcher.update_stats()
            
            if self.max_results is not None and count >= self.max_results:
                break
    
    def update_empty_orcid(self, researcher, val):
        """
        Updates the empty_orcid_profile field of the provided :class:`Researcher` instance.
        This is sent to the clustering context factory where a batch reclustering is performed
        if needed. The relevance score of papers depend on whether we have found at least one
        paper associated to the researcher via ORCID, hence we need this reclustering when
        we discover such a paper.
        """
        if val != researcher.empty_orcid_profile:
            researcher.empty_orcid_profile = val
            researcher.save(update_fields=['empty_orcid_profile'])
            self.ccf.updateResearcher(researcher)



