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

Fixtures
--------

Dissemin comes with some fixtures predefined. There are mainly two types:

1. Fixtures coming from ``load_test_data``
2. Pure python fixtures in ``conftest.py``

While the first class of fixtures laods a lot of data into the test database, they are not always suitable and little obscur. We encourage you not to use them except it is necessary.

The second class is not yet completed. You find some fixtures in the projects root. You can add more fixtures as you need them. If your fixture is only suitable or interesting for a single app, please use it's ``conftest.py``.

So, for example, if you need more repositories or with special properties, add the corresponding function into the ``Dummy`` class of the fixture ``repository``. If you want to use this new repository often out of the box, add a new fixture, that gets it from the ``Dummy`` class as shown with the ``dummy_repository`` fixture.

The benefit of the second approach is more control and better extensibility.

Mocking
-------

Currently we partially use mocking. If you write any new test, please use a proper mocking.
