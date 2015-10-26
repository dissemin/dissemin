.. _page-datasources:

Data sources
============

Dissemin works with various data sources, providing bibliographic
references, full texts and publisher's policies. Most of these sources
only provide a search API to expose their data: we do not store a copy
of their database but perform calls to their external API when required.
This has the advantage of keeping the local data storage needs very modest,
but fetching the appropriate data from the APIs takes some time.

CrossRef
--------

CrossRef is an association of publishers, mainly in charge of issuing Digital
Object Identifiers (DOIs) for academic publications. DOIs provide many useful
features:

* Redirection to the publication's page on the publisher's website, with links
  of the form `http://dx.doi.org/10.1103/physreve.89.033013 <http://dx.doi.org/10.1103/physreve.89.033013>`_.
  When a publisher changes the structure of its website, tells CrossRef where
  the resources have moved, updating the DOI proxy so that users are redirected
  to the new location.
* Associating metadata to DOIs, in a uniform format. The metadata associated with
  a given DOI can be retrieved using `content negociation <https://en.wikipedia.org/wiki/Content_negotiation>`_. This is useful to get the metadata associated with a DOI that we discover
  from other metadata sources. It works as follows::

    $ curl -LH "Accept: application/citeproc+json" http://dx.doi.org/10.1103/physreve.89.033013 
    {
        "indexed":
        {
            "date-parts": [[2015,6,10]],
            "timestamp": 1433897719282
        },
        "reference-count": 36,
        "publisher": "American Physical Society (APS)",
        "issue": "3",
        "license":[
            {
                "content-version": "vor",
                "delay-in-days": 13,
                "start": {
                    "date-parts": [[2014,3,14]],
                    "timestamp": 1394755200000
                },
                "URL": "http://link.aps.org/licenses/aps-default-license"
            }

        ],
        "DOI": "10.1103/physreve.89.033013",
        "type": "journal-article",
        "source": "CrossRef",
        "title": "Small-scale anisotropic intermittency in magnetohydrodynamic turbulence at low magnetic Reynolds numbers",
        "prefix": "http://id.crossref.org/prefix/10.1103",
        "volume": "89",
        "author": [
            {
                "affiliation": [ ],
                "family": "Okamoto",
                "given": "Naoya"
            },
            {
                "affiliation": [ ],
                "family": "Yoshimatsu",
                "given": "Katsunori"
            },
            {
                "affiliation": [ ],
                "family": "Schneider",
                "given": "Kai"
            },
            {
                "affiliation": [ ],
                "family": "Farge",
                "given": "Marie"
            }

        ],
        "member": "http://id.crossref.org/member/16",
        "container-title": "Physical Review E",
        "link": [
            {
                "intended-application": "syndication",
                "content-version": "vor",
                "content-type": "unspecified",
                "URL": "http://link.aps.org/article/10.1103/PhysRevE.89.033013"
            }
        ],
        "deposited": 
        {
            "date-parts":[[2015,4,13]],
            "timestamp": 1428883200000
        },
        "score": 1,
        "subtitle": [ ],
        "issued": 
        {
            "date-parts":[[2014,3]]
        },
        "URL": "http://dx.doi.org/10.1103/physreve.89.033013",
        "ISSN": 
        [
            "1539-3755",
            "1550-2376"
        ],
        "subject": 
            [
                "Condensed Matter Physics",
                "Statistical and Nonlinear Physics",
                "Statistics and Probability"
            ]
    }

* A search API, basically a machine-readable version of `CrossRef Metadata Search <http://search.crossref.org>`_. Similar metadata is returned for each search result. The documentation can be found `here <https://github.com/CrossRef/rest-api-doc/blob/master/rest_api.md>`_. By searching for an researcher's name and browsing through the few first results pages, we get the metadata for most papers written by that researcher and registered at CrossRef.
  This service only returns DOIs issued by CrossRef, the two other services also work for other DOI
  registration agencies such as DataCite or MEDRA.


SHERPA/RoMEO
------------

TODO

ORCID
-----

TODO

BASE and CORE
-------------

TODO

Proaixy
-------

TODO


