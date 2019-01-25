.. _page-datamodel:

The data model in Dissemin
==========================

This section explains how metadata is represented in Dissemin. There are two
important models: ``OaiRecord`` and ``Paper`` (both defined in
``papers/models.py``).

The ``OaiRecord`` model represents an occurence of a paper in some external
repository (from the publisher or from an open repository). Each ``OaiRecord``
has at least a ``splash_url`` (the URL of the landing page of the paper in the
repository) and sometimes a ``pdf_url``. The ``pdf_url`` is present if and only
if we think that the full text is available from this repository. This
``pdf_url`` should ideally be a direct link to the full text, but often it is
actually equal to the ``splash_url`` (but its presence still indicates that the
full text is available somehow).

These records are grouped into ``Paper`` objects (via a foreign key from
``OaiRecord`` to ``Paper``). This deduplication process is done by two
criteria:

* first, ``OaiRecords`` with the same DOI are merged into the same paper.
* second, we compute a fingerprint of the ``OaiRecord`` metadata, which
  consists of the title, author last names and publication year. Any two
  ``OaiRecords`` with identical fingerprints are also merged into the same
  ``Paper``.

Dissemin :ref:`harvests four metadata sources <page-datasources>`: ORCID,
Crossref, BASE and Unpaywall (oadoi). Each of these implements the
``PaperSource`` interface, which provides mechanisms to push the papers to the
database. The responsibility of each ``PaperSource`` is to provide
``BarePaper`` instances, which are Python objects representing papers which
have not been saved to the database yet (and therefore not deduplicated). When
doing this, each ``PaperSource`` determines from the medatada they have access
to whether ``pdf_url`` should be filled or not (depending on whether we think
the metadata indicates full text availability).
