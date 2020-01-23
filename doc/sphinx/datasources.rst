.. _page-datasources:

============
Data sources
============

Dissemin works with various data sources, providing bibliographic references, full texts and publisher's policies.

CrossRef
========

CrossRef is an association of publishers, mainly in charge of issuing Digital Object Identifiers (DOIs) for academic publications.
We harvest the CrossRef API on a daily basis.

CrossRef is our main source of publications.
On harvesting, we try to match the journal with information from SHERPA/RoMEO.

BASE
====

`BASE <https://www.base-search.net/>`_ is a search machine for academic publications. BASE harvests several thousand free and open repositories. We use BASE to extend the information of full text availability. It covers a huge amount of green open access publications.

SHERPA/RoMEO
============

`SHERPA/RoMEO <http://www.sherpa.ac.uk/romeo/>`_ is a service run by `JISC <https://www.jisc.ac.uk/>`_ which provides a semi-structured representation of publisher's self-archiving policies.
They offer `an API <http://www.sherpa.ac.uk/romeo/apimanual.php?la=en&fIDnum=|&mode=simple>`_, whose functionality is very similar to the search service they offer to their regular users.
You can search for a policy by journal or by publisher.
Since some publishers have multiple archiving policies, RoMEO recommends to search by journal because it ensures that you will get the policy in place for this specific journal.

We synchronize our data with SHERPA's data every two weeks using `their dumps <http://www.sherpa.ac.uk/downloads>`_.

For many journal articles and all conference papers, RoMEO knows the publisher but not the journal, and the metadata returned by CrossRef contains both the journal (or the proceedings title) and the publisher.
We use therefore a two-step approach:

* We search for the journal: if it succeeds, we assign the journal and the corresponding policy to the paper.
* If it fails, we search for the a default policy from the publisher.
  Default policies are those which have a null ``romeo_parent_id``.

Because the publisher names are not always the same in CrossRef and SHERPA/RoMEO, we add heuristics to disambiguate publishers.
We use the papers for which a corresponding journal was found in SHERPA and collect their publisher names as seen in Crossref.
If we see that a given Crossref publisher name is overwhelmingly associated to a given SHERPA Publisher which is a default publisher policy (``romeo_parent_id`` is null), then we also link Crossref papers with this publisher name but no matching journal to this SHERPA Publisher.

ORCID
=====

ORCID has a public API that can be used to fetch the metadata of all papers ("works") made visible of any ORCID profile (unfortunately, very often, the profiles are empty).
ORCID does not enforce any strict metadata format, which makes it hard to import papers in Dissemin. Specifically, works do not always have a list of authors (which is a shame given that this service is supposed to solve ambiguity of author names).
Even worse, when an authors list is provided, the owner of the ORCID record is almost never identified in this list.

We try to make the most of the available metadata:

* If a DOI is present, we fetch the metadata using content negociation ;
* If a Bibtex version of the metadata is available, parse the Bibtex record to extract the title and author names ;
* Otherwise, if no authors are given, skip the paper.
