# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#



import logging

from celery import shared_task
from datetime import date

from backend.utils import run_only_once
from deposit.models import DepositRecord

logger = logging.getLogger('dissemin.' + __name__)


@shared_task(name='refresh_deposit_statuses')
@run_only_once('refresh_deposit_statuses')
def change_embargoed_to_published():
    """
    This function changes all DepositRecord with status ``embargoed`` to ``published`` with today ``publication_date``
    """
    n = DepositRecord.objects.filter(status='embargoed', pub_date__lte=date.today()).update(status='published')
    logger.info("Changed deposit status from 'embargoed' to 'published' for {} DepositRecords".format(n))



@shared_task(name='refresh_deposit_statuses')
@run_only_once('refresh_deposit_statuses')
def refresh_deposit_statuses():
    # only run it on DepositRecords that have initially succeeded:
    # ignore 'failed' and 'faked' statuses
    for d in DepositRecord.objects.filter(status__in=
            ['pending','published','refused','deleted']).select_related('repository'):
        logger.info(d.status)
        protocol = d.repository.get_implementation()
        if protocol:
            protocol.refresh_deposit_status(d)
