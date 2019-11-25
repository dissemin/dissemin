===============
Technical Scope
===============

In this document we describe the technical part of adding a new repository.
For now we describe the `SWORDv2 protocol <http://swordapp.org/sword-v2/sword-v2-specifications/>`_, but we are not bound to this transmission form.

SWORDv2
=======

To some extend the SWORDv2 protocl is easy to use as it involes just some basic HTTP stuff.
We decided to use its packaging capability, because this way we can easily ship metadata and document at the same time.

METS
----

We use the `Metdata Encoding \& Transmission Standard (METS) <https://www.loc.gov/standards/mets/>`_ to ship our metadata and describe what is delivered.
Most repositories are able to ingest a METS-package.

We try to keep our METS as simple as possible.
Currently we populate only ``dmdSec``, ``amdSec/rightsMD``, ``fileSec`` and ``structSec``.

* ``dmdSec`` contains the bibliographic metadata
* ``amdSec/rightsMD`` contains information about the depositor, the license and additional dissemin related information. You find the documentation in :ref:`non-bibliographic-metadata-label`.

We deliver two files per package:

* ``mets.xml`` - containing the metadata
* ``document.pdf`` - the document to be deposited

We provide an :download:`illustrating example <examples/mets.xml>` using Dublin Core.

We set the following headers::

    Content-Type: application/zip
    Content-Disposition: filename=mets.zip
    Packaging: http://purl.org/net/sword/package/METSMODS

If you require for your ingest a different packaging name or packaging format, please let us know.

MODS
----

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

We ship the language as rfc3066 determined by `langdetect <https://pypi.org/project/langdetect/>`_ and only if both conditions are satisfied:

1. The abstract has a length of at least 256 letters (including whitespaces)
2. ``langdetect`` gains a confidence of at least 50%

If we cannot determine any language, we omit the field.

We ship the ddc number as three-digit-number, i.e. filling up with leading zeros for numbers smaller than 99.


Dissemin Metadata
-----------------

MODS does not completely fit our needs in term of metadata.
Thus we add our own metadata that extends the MODS metadata.

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
embargoDate           The publication must not be published before this date. It may be published on this date.
SHERPA/RomeoID        ID of the journal from `SHERPA/RoMEO <http://sherpa.ac.uk/romeo/index.php>`_. Using their API or web interface you can quickly obtain publishers conditions.
DisseminID            This ID refers to the publication in Dissemin. This ID is not persistent. The reason is the internal data model: Merging and unmerging papers might create or delete primary keys in the database. For a 'short' period of time, this id will definetely be valid. You can use the DOI shipped in the bibliographic metadata to get back to the publication in Dissemin.
===================== =====

If you need more information for your workflow, please contact us. We can add additional fields.

You can find our schema for :download:`download <../../deposit/schema/dissemin_v1.0.xsd>` in Version 1.0.

Examples and Scripts
--------------------

To support you in your local implementation we have some examples and scripts.

Examples
~~~~~~~~
The metadata is authentic, i.e. it is created with Dissemin and represents how the metadata documents will loke like.
For earch document type there is one or more example.
They cover different cases like dewey decimal class or embargo.

* :download:`MODS <examples/mods.zip>`


Upload scripts
~~~~~~~~~~~~~~

You can download our :download:`script <examples/upload_mets.zip>` for testing your implementations.
The HTTP-request is identical to that in Dissemin.
You find usage instructions in the README.md inside of the packaging.


Repository Helpers
==================

We cannot support any direct support for necessary implementations or configurations on the repository that is going to be connected.

But we like to support any repository administrator with at least some documentation.

EPrints 3
---------

EPrints 3 has been successfully be connected to Dissemin.

Zaharina Stoynova from ULB Darmstadt has worked on a plugin to ingest Dissemins metadata.
As it is probably not possible to use it directly, please make the necessary changes as you require.

:download:`broker_eprints_3.zip <examples/broker_eprints_3.zip>`

The package consists of two files:

1. `METSMODS_Broker.pm`
2. `METSMODS_Brokder_mods_parser.pm`

The first file deals with some general things like data integrity and ingests the Dissemin metadata, while the other file deals with the MODS metadata itself.
