.. _page-apikeys:
Getting API keys
================

Dissemin relies on various interfaces to fetch its metadata.
Some of them require to register for an API key, that dissemin
reads in ``dissemin/settings.py``, the main configuration file.

Here is how to register for these interfaces.

SHERPA/RoMEO
------------

`SHERPA/RoMEO <http://www.sherpa.ac.uk/romeo>`_ gives a machine-readable to publishers' self-archiving
policies.

The API key is not required but encoraged as unauthenticated users
can perform a limited number of queries daily.

To get an API key, visit `this page <http://www.sherpa.ac.uk/romeo/apiregistry.php>`_.
The key should then be written in ``dissemin/settings.py``, as ``ROMEO_API_KEY``.

CORE
----

`COnnecting REpositories (CORE) <http://core.ac.uk>`_ is a preprint search engine that harvests not only
metadata but also full texts. It is used internally to discover full texts.
By default, CORE is not enabled, as we have observed that it is quite slow and does
not provide many relevant results.

An API key is required to use the CORE API.
You can get one `here <http://core.ac.uk/api-keys/register>`_.

BASE
----

`Bielefeld Academic Search Engine (BASE) <http://www.base-search.net>`_ is a preprint search
engine that only harvests metadata but has a wider coverage than CORE. It is also used to discover
full texts. It is activated by default.

To use the BASE interface, you need to register the IP address of your server first.
This can be done by `sending a message to the BASE team <http://www.base-search.net/about/en/contact.php>`_.

Zenodo
------

`Zenodo <http://zenodo.org>`_ is a repository hosted by CERN, storing publications as well as
research data. Dissemin uses it to upload papers on behalf of users.

To use Zenodo, you need `an account <https://zenodo.org/youraccount/register>`_. You can
then generate an auth token from their web interface.
Then, set up the repository via the Dissemin admin interface (available at /admin). 

