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

Zenodo
------

`Zenodo <https://zenodo.org>`_ is a repository hosted by CERN, storing publications as well as
research data. Dissemin uses it to upload papers on behalf of users.

To use Zenodo, you need `an account <https://zenodo.org/youraccount/register>`_. You can
then generate an auth token from their web interface.
Then, set up the repository via the Dissemin admin interface (available at /admin). 

Proaixy
-------

Proaixy is an OAI-PMH proxy where disemin discovers preprints.
For now, no API key is required to use this service.

