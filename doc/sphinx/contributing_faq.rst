.. _page-contributing_faq:

FAQ for contributing to Dissemin
================================

Here are some frequently asked questions and tips for getting started to work and contribute to Dissemin. The best idea to start hacking on Dissemin is probably to use the VM (Vagrant method from :ref:`page-install`).

Fetching a specific paper by DOI
--------------------------------

The Dissemin VM is quite empty by default. If you want to inspect particular paper, it is possible to fetch
it by DOI by visiting ``http://localhost:8080/<DOI>``.

Fetching a specific ORCID profile
---------------------------------

The Dissemin VM uses the sandbox ORCID API out of the box. Therefore, you cannot fetch a specific profile from ORCID. Here is how to locally fetch a specific profile from ORCID, in order to reproduce and debug bugs in fetching the list of papers for instance.

First, edit the ``dissemin/settings/__init__.py`` file to set the ORCID API to use to the real ORCID API, putting the line ``ORCID_BASE_DOMAIN = 'orcid.org'``.

Then, you should find the ORCID ID you want to fetch locally. You can use the official instance, https://dissem.in/, to search for a given author and get the ORCID ID.

Finally, restart both the Django process as well as the Celery process in the VM and head to ``http://localhost:8080/<ORCID_ID>``, replacing ``<ORCID_ID>`` by the full ORCID ID.
