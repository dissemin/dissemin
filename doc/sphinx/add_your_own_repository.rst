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
Currently we populate only ``dmdSec``, ``amdSec/rightsMD``, ``fileSec`` and ``structSec``.

* ``dmdSec`` contains the bibliographic metadata
* ``amdSec/rightsMD`` contains information about the depositor, the license and additional dissemin related information. You find the documentation in :ref:`non-bibliographic-metadata-label`.

We deliver two files per package:

* ``mets.xml`` - containing the metadata
* ``document.pdf`` - the document to be deposited

We provide an :download:`illustrating example <examples/mets.xml>` using Dublin Core.


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
    author => name[@type="personal"]namePart/given + family + name
    author[orcid] => name/nameIdentifier[@type=orcid]
    date => originInfo/dateIssued[@enconding="w3cdtf"] (YYYY-MM-DD)
    ddc => classification[@authority="ddc"]
    document type => genre
    doi => identifier[@type="doi"]
    essn => relatedItem/identifier[@type="eissn"]
    issn => relatedItem/identifier[@type="issn"]
    issue => relatedItem/part/detail[@type="issue"]/number
    journal => relatedItem/titleInfo/title
    language => language/languageTerm[@type="code"][@authority="rfc3066"]
    pages => relatedItem/part/extent[@unit="pages"]/total or start + end
    publisher => originInfo/publisher
    title => titleInfo/title
    volume => relatedItem/part/detail[@type="volume"]

Note that volume, issue and pages are often not arabic numbers, but may contain other literals.
Although MODS does provide fields for declarations like *No., Vol.* or *p.* we do not use this, because our datasources don't.

We ship the language as rfc3066 determined by `langdetect <https://pypi.org/project/langdetect/>`_.
We ship the language if both conditions are satisfied:

1. The abstract has a length of at least 256 letters (including whitespaces)
2. ``langdetect`` gains a confidence of at least 50%

If we cannot determine any language, we omit the field.

Optionally we ship the Dewey Decimal Class (DDC).
We support up to the first 1000 classes, i.e. from ``000`` to ``999``.
You can freely chose which classes are of interest.
When presenting the user, we group them with categories ``0...9``.
We ship the classification number as three-digit-number, i.e. filling up with leading zeros for numbers smaller than 99.

Examples
........

This is our list of examples of MODS metadata created by Dissemin.
This includes, that they are already contained in a suitable METS container.
The list is sorted by publications types and covers all publication types that Dissemin uses.

.. include:: examples/mods/examples_mods.rst

.. _non-bibliographic-metadata-label:

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
license               The license. Most likely Creative Commons, but different licenses are possible. We happily add new licenses for your repository. We deliver the name and if existing URI and a transmit id.
SHERPA/RomeoID        ID of the journal from `SHERPA/RoMEO <http://sherpa.ac.uk/romeo/index.php>`_. Using their API or web interface you can quickly obtain publishers conditions.
DisseminID            This ID refers to the publication in Dissemin. This ID is not persistent. The reason is the internal data model: Merging and unmerging papers might create or delete primary keys in the database. For a 'short' period of time, this id will definetely be valid. You can use the DOI shipped in the bibliographic metadata to get back to the publication in Dissemin.
===================== =====

If you need more information for your workflow, please contact us. We can add additional fields.

You can find our schema for :download:`download <../../deposit/schema/dissemin_v1.0.xsd>` in Version 1.0.


Letter of Declaration
---------------------

To finally publish a document or resource in your repository, you might require some kind of letter of declaration of the depositor, in which the depositors sign that he accepts certain conditions etc. pp.

Dissemin can generate these type of letters individually per repository, i.e. you can define the content and look of this document.
Additionally it is prefilled with all necessary data, so that the depositor just has to sign and send you the letter.

After the deposit the depositor is informed that he has to fill in such a letter and send it to your repository administration. He can directly download this letter. En plus he can regenerate this letter at any point in time as long you haven't published the resource.

We provide an :download:`example letter of declaratio n<examples/letter_of_declaration_ulb_darmstadt.pdf>` of ULB Darmstadt, so you have some imagination how it finally looks like.
