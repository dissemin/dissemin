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
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#


from __future__ import unicode_literals

from django.db import models
from django import forms
from django.utils.translation import ugettext as __
from django.conf import settings

import traceback, sys, requests

from papers.models import *

class DepositError(Exception):
    """
    The exception to raise when something wrong happens
    during the deposition process
    """
    def __init__(self, msg):
        super(DepositError, self).__init__(msg)

class EmptyForm(forms.Form):
    pass

class DepositResult(object):
    """
    Small object containing the result of a deposition process.
    This object will be stored in two rows in the database:
    in an OaiRecord and in a DepositRecord.
    """
    def __init__(self, identifier=None, splash_url=None, pdf_url=None, logs=None,
            status='SUCCESS', message=None):
        self.identifier = identifier
        self.splash_url = splash_url
        self.pdf_url = pdf_url
        self.logs = logs
        self.status = status
        self.message = message

    def success(self):
        """
        Returns whether the deposit was successful.
        """
        return self.status == 'SUCCESS'

class RepositoryProtocol(object):
    """
    The protocol for a repository where papers can be deposited.
    Actual implementations should inherit from this class.
    """

    def __init__(self, repository, **kwargs):
        self.repository = repository
        self._logs = None
        self.paper = None
        self.user = None

    def protocol_identifier(self):
        """
        Returns an identifier for the protocol.
        """
        return type(self).__name__

    def init_deposit(self, paper, user):
        """
        Called when a user starts considering depositing a paper to a repository.

        :param paper: The paper to be deposited.
        :param user: The user submitting the deposit.
        :returns: a boolean indicating if the repository can be used in this case.
        """
        self.paper = paper
        self.user = user
        self._logs = ''
        return True

    def get_form(self):
        """
        Returns the form where the user will be able to give additional metadata.
        """
        return EmptyForm()

    def get_bound_form(self, data):
        """
        Returns a bound version of the form, with the given data.
        """
        return EmptyForm()

    def submit_deposit(self, pdf, form):
        """
        Submit a paper to the repository.
        This is expected to raise DepositError if something goes wrong.

        :param pdf: Filename to the PDF file to submit
        :param form: The form returned by get_form and completed by the user.
        :returns: a DepositResult object.
        """
        raise NotImplemented('submit_deposit should be implemented in the RepositoryInterface instance.')

    def submit_deposit_wrapper(self, *args):
        """
        Wrapper of the submit_deposit method (that should not need to be
        reimplemented). It catches DepositErrors raised in the deposit process
        and adds the logs to its return value.
        """
        try:
            result = self.submit_deposit(*args)
            result.logs = self._logs

            # Create the corresponding OAI record
            OaiRecord.new(
                    source=self.repository.oaisource,
                    identifier=('deposition:%d:%s' %
                        (self.repository.id, unicode(result.identifier))),
                    about=self.paper,
                    splash_url=result.splash_url,
                    pdf_url=result.pdf_url)

            self.paper.update_author_stats() # TODO write an unit test for this
            return result
        except DepositError as e:
            self.log('Message: '+e.args[0])
            return DepositResult(logs=self._logs,status='FAILED',message=e.args[0])
        except Exception as e:
            self.log("Caught exception:")
            self.log(str(type(e))+': '+str(e)+'')
            self.log(traceback.format_exc())
            return DepositResult(logs=self._logs,status='FAILED',message=__('Failed to connect to the repository. Please try again later.'))


    def log(self, line):
        """
        Logs a line in the protocol log.
        """
        self._logs += line+'\n'

    def log_request(self, r, expected_status_code, error_msg):
        """
        Logs an HTTP request and raises an error if the status code is unexpected.
        """
        self.log('--- Request to %s\n' % r.url)
        self.log('Status code: %d (expected %d)\n' % (r.status_code, expected_status_code))
        if r.status_code != expected_status_code:
            self.log('Server response:')
            self.log(r.text)
            self.log('')
            raise DepositError(error_msg)



