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

from papers.models import Paper
from papers.models import Researcher


class PaperSource(object):
    """
    Abstract interface for something that adds papers from some metadata source
    for a given researcher.
    """

    def __init__(self, max_results=None):
        """
        A PaperSource can be used without saving the papers
        to the database, using :func:`fetch_bare`.

        Subclasses can reimplement the constructor to get parameters for the source.
        Do not forget to call this base constructor though.

        :param max_results: maximum number of papers to retrieve for each researcher.
        """
        self.max_results = max_results

    def fetch_papers(self, researcher):
        """
        This function is the one subclasses should reimplement.
        Given a researcher, it should yield all the papers it can
        fetch from the source.
        """
        raise NotImplementedError(
            "fetch_papers should be implemented by the subclass")

    def fetch_bare(self, researcher):
        """
        This function returns a generator of :class:`BarePaper` fetched for the
        given researcher.
        """
        return self.fetch_papers(researcher)

    def fetch_and_save(self, researcher):
        """
        Fetch papers and save them to the database.

        :param incremental: When set to true, papers are clustered
            and commited one after the other. This is useful when
            papers are fetched on the fly for an user.
        """
        count = 0
        for p in self.fetch_bare(researcher):
            try:
                self.save_paper(p, researcher)
            except ValueError:
                continue
            if self.max_results is not None and count >= self.max_results:
                break

            count += 1

    def save_paper(self, bare_paper, researcher):
        # Save the paper as non-bare
        p = Paper.from_bare(bare_paper)

        # Associate known ORCIDs to the corresponding researchers
        for idx, author in enumerate(p.authors_list):
            if author['orcid']:
                try:
                    researcher = Researcher.objects.get(orcid=author['orcid'])
                    p.set_researcher(idx, researcher.id)
                except Researcher.DoesNotExist:
                    p.set_researcher(idx, None)
            else:
                p.set_researcher(idx, None)

        p.save()
        p.update_index()

        return p

    def update_empty_orcid(self, researcher, val):
        """
        Updates the empty_orcid_profile field of the provided :class:`Researcher` instance.
        """
        if val != researcher.empty_orcid_profile:
            researcher.empty_orcid_profile = val
            researcher.save(update_fields=['empty_orcid_profile'])

