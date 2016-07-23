# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#


from __future__ import unicode_literals

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from pyvirtualdisplay import Display
from django.conf import settings
import os

RUN_LOCAL = (not os.environ.get('TRAVIS')) or os.environ.get('LOCAL_SELENIUM')

class SeleniumTest(StaticLiveServerTestCase):
    fixtures = ['oauth_orcid.json']

    @classmethod
    def setUpClass(cls):
        super(SeleniumTest, cls).setUpClass()
        settings.DEBUG = True
        if RUN_LOCAL:
            cls.display = Display(visible=0, size=(800,600))
            cls.display.start()
            cls.selenium = webdriver.firefox.webdriver.WebDriver()
            cls.selenium.implicitly_wait(10) # seconds
        else:
            # inspired from
            # https://github.com/Victory/django-travis-saucelabs/blob/master/mysite/saucetests/tests.py
            capabilities = {
                'name': cls.__name__,
                'tunnel-identifier': os.environ.get('TRAVIS_JOB_NUMBER'),
                'build': os.environ.get('TRAVIS_BUILD_NUMBER'),
                'tags': [
                    os.environ.get('TRAVIS_PYTHON_VERSION'),
                    'Travis',
                    ],
                'platform':'Linux',
                'browserName':'firefox',
                'version':'38',
                }
            username = os.environ.get('SAUCE_USERNAME')
            access_key = os.environ.get('SAUCE_ACCESS_KEY')
            sauce_url = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub"
            cls.selenium = webdriver.Remote(
                    desired_capabilities=capabilities,
                    command_executor=sauce_url % (USERNAME, ACCESS_KEY))

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        if RUN_LOCAL:
            cls.display.stop()
        super(SeleniumTest, cls).tearDownClass()

    def get_relative(self, relative_url):
        self.selenium.get('%s%s' % (self.live_server_url, relative_url))

    def by_css(self, css_selector):
        return self.selenium.find_element_by_css_selector(css_selector)

    def by_id(self, id):
        return self.selenium.find_element_by_id(id)

    def by_xpath(self, xp):
        return self.selenium.find_elements_by_xpath(xp)

    def test_oauth_login(self):
        # Go to the login page and click login
        self.get_relative('/accounts/login/')
        login_button = self.by_css('.left .btn-orcid')
        login_button.click()
        # Fill the ORCID login form
        self.by_id('userId').send_keys('liethpeter@mailinator.com')
        self.by_id('password').send_keys('liethpeter0')
        # self.by_id('enablePersistentToken').click() # uncheck
        self.by_id('login-authorize-button').click()
        # Check that the name of the user is present
        name_elem = self.by_xpath("//*[contains(text(), 'P. Lieth')]")
        self.assertTrue(name_elem[0])


