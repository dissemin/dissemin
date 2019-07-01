Add your own Repository
=======================

If you like to add your (institutional) repository, please get in contact with us. On this page we offer you some information about our services and what has to be done on your side.

Currently we work on implementations for EPrints, MyCore and DSpace.

Deposition Protocol
-------------------

Currently we support the `SWORDv2 protocol <http://swordapp.org/sword-v2/sword-v2-specifications/>`_. However, this protocol offers a lot of options about how to deposit and how to organize the metadata and should be seen as a framework. Technically we can offer different depositing methods, e.g. via some REST API or similar.

Metadata
--------

We use the `Metdata Encoding \& Transmission Standard (METS) <https://www.loc.gov/standards/mets/>`_ to ship our metadata and describe what is delivered. Most repositories are able to ingest a METS-package.

We try to keep our METS as simple as possible.
Currently we populate only ``dmdSec``, ``fileSec`` and ``structSec``.
We deliver two files per package:

* ``mets.xml`` - containing the metadata
* ``document.pdf`` - the document to be deposited

Bibliographic Metadata
^^^^^^^^^^^^^^^^^^^^^^

Most of our data comes from `CrossRef <https://www.crossref.org>`_ and has thus a certain quality. 

We offer currentlry `Metadata Objects Description Data (MODS) <http://www.loc.gov/standards/mods/>`_.

MODS
''''

Currently we create version ``3.7``. 
We populate as near as the definitions require as possible.
You find below our mappings using XPath notation.

.. code::

    abstract => abstract
    author => name/personal/namePart/given + family
    date => originInfo/dateIssued[@enconding="w3cdtf"] (YYYY-MM-DD)
    document type => genre
    doi => identifier[@type="doi"]
    essn => relatedItem/identifier[@type="eissn"]
    issn => relatedItem/identifier[@type="issn"]
    issue => relatedItem/part/detail[@type=issue]/number
    journal => relatedItem/titleInfo/title
    pages => relatedItem/part/extent[@unit="pages"]/total or start + end
    publisher => originInfo/publisher
    title => titleInfo/title
    volume => relatedItem/part/detail[@type="volume"]

Note that volume, issue and pages are often not arabic numbers, but may contain other literals.
Although MODS does provide fields for declarations like *No., Vol.* or *p.* we do not use this, because our datasources don't.

Examples
........

This is our list of examples of MODS metadata created by Dissemin.
This includes, that they are already contained in a suitable METS container.
The list is sorted by publications types and covers all publication types that Dissemin uses.

.. include:: examples/mods/examples_mods.rst

Non-Bibliographic Metadata
^^^^^^^^^^^^^^^^^^^^^^^^^^

In addition to our bibliographic metadata we ship non-bibliographic metadata. This metadata is meant to support publication workflows in institutional repositories, for example helping in the moderation process.

We ship the following data:

===================== =====
Data                  Explanation
===================== =====
authentication method The method of authentication. This is currently shibboleth and orcid.
name                  The first and last name of the depositor. Note that the depositor does not need to be a contributor of the publication.
email                 E-Mail address of the depositor in case you need to contact them.
orcid                 ORCID if the depositor has one.
is contributor        ``true/false`` and states if the depositor is one of the contributors or if deposits on behalf
identical institution ``true/false`` and states if the depositors institution is identical with the institution of the repository.
license               The license. Most likely Creative Commons, but different licenses are possible. We happily add new licenses for your repository. We deliver the name and if existing URI and short name like CC BY 4.0.
SHERPA/RomeoID        ID of the journal from `SHERPA/RoMEO <http://sherpa.ac.uk/romeo/index.php>`_. Using their API or web interface you can quickly obtain publishers conditions.
DisseminID            This ID refers to the publication in Dissemin. This ID is not persistent. The reason is the internal data model: Merging and unmerging papers might create or delete primary keys in the database. For a 'short' period of time, this id will definetely be valid. You can use the DOI shipped in the bibliographic metadata to get back to the publication in Dissemin.
===================== =====

If you need more information for your workflow, please contact us. We can add additional fields.

You can find our schema for :download:`download <../../deposit/schema/dissemin_v1.0.xsd>` in Version 1.0.



