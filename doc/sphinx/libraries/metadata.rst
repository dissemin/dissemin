========
Metadata
========

Our main data sources are CrossRef and BASE.
Our own data scheme is relatively close to Citeproc / CrossRef.
This gives us the advantage, that---in general---we do not need to ask the user for metadata.
This makes a deposit very little effort.

Bibliographic Metadata
======================

For a publication we store the following metadata.

.. code::

    abstract
    authors
    date (YYYY-MM-DD)
    document type
    doi
    eissn
    issn
    issue
    journal
    language
    pages
    publisher
    title
    volume

Note however, that we have renamed Citeprocs `container-title` into `journal`.
This has a historical reason, aiming at first at journal articles.

Document types
==============

We have the following document types:

.. code::

    book
    book-chapter
    dataset
    journal-article
    journal-issue
    poster
    preprint
    proceedings
    proceedings-article
    reference-entry
    report
    thesis
    other

Almost 90 per cent of our deposits are journal articles.

Additional Metadata
===================

In addition to the above metadata we can ship out of the box the following:

.. code::

    depositor information (name, email, orcid)
    dewey decimal class
    embargo
    language (with langdetect)
    license
    sherpa romeo id
