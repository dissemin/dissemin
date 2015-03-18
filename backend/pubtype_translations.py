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

from __future__ import unicode_literals

# arXiv: they are all 'text'
# DOAJ: all 'article'

PUBTYPE_TRANSLATIONS = {
        # HAL:


        }

SET_TO_PUBTYPE = {
        # HAL:
        'type:ART':'journal-article',
        'type:COMM':'proceedings-article',
        'type:COUV':'book-chapter',
        'type:DOUV':'proceedings',
        'type:HDR':'thesis',
        'type:IMG':'other',
        'type:LECTURE':'other',
        'type:MAP':'other',
        'type:OTHER':'other',
        'type:OUV':'book',
        'type:PATENT':'other',
        'type:POSTER':'poster',
        'type:REPORT':'report',
        'type:SON':'other',
        'type:THESE':'thesis',
        'type:UNDEFINED':'other',
        'type:VIDEO':'other',

        }

