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

from django.conf.urls import include, url

from deposit import views

urlpatterns = [
        url(r'^deposit_paper/(?P<pk>\d+)/$', views.start_view, name='upload_paper'),
        url(r'^ajax/submit-deposit-(?P<pk>\d+)$', views.submitDeposit, name='ajax-submitDeposit'),
        url(r'^ajax/get-metadata-form$',
                views.get_metadata_form, name='ajax-getMetadataForm'),
]
