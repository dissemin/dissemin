# This code was taken from http://stackoverflow.com/questions/5917587/django-unit-tests-without-a-db

from django.test.runner import DiscoverRunner

class BareTestRunner(DiscoverRunner):
  """ A test runner to test without database creation """

  def setup_databases(self, **kwargs):
    """ Override the database creation defined in parent class """
    pass

  def teardown_databases(self, old_config, **kwargs):
    """ Override the database teardown defined in parent class """
    pass
