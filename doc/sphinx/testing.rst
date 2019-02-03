.. _page-docs:

Testing dissemin
================

Dissemin's test suite is run using ``pytest`` rather than using Django's ``./manage.py test``.
Pytest offers many additional features compared to Python's standard ``unittest`` which
is used in Django. To run the test suite, you need to install pytest and other packages,
mentioned in ``requirements-dev.txt``.

The test suite is configured in ``pytest.ini``, which determines which files are scanned
for tests, and where Django's settings are located.

Some tests rely on remote services. Some of them require API keys, they will fetch them
from the following environment variables (or be skipped if these environment variables are
not defined):
* ``ROMEO_API_KEY`` 
* ``ZENODO_SANDBOX_API_KEY`` required for tests of the Zenodo interface. This can be obtained
  by creating an account on sandbox.zenodo.org and creating a "Personal Access Token" from there.

