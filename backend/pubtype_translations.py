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



# arXiv: they are all 'text'
# DOAJ: all 'article'

OAI_PUBTYPE_TRANSLATIONS = {
        # Our own typology
        'journal-article': 'journal-article',
        'proceedings-article': 'proceedings-article',
        'book-chapter': 'book-chapter',
        'book': 'book',
        'journal-issue': 'journal-issue',
        'proceedings': 'proceedings',
        'reference-entry': 'reference-entry',
        'poster': 'poster',
        'report': 'report',
        'thesis': 'thesis',
        'dataset': 'dataset',
        'preprint': 'preprint',
        'other': 'other',
        # OpenAIRE
        'info:eu-repo/semantics/article': 'journal-article',
        'info:eu-repo/semantics/bachelorThesis': 'thesis',
        'info:eu-repo/semantics/masterThesis': 'thesis',
        'info:eu-repo/semantics/doctoralThesis': 'thesis',
        'info:eu-repo/semantics/book': 'book',
        'info:eu-repo/semantics/bookPart': 'book-chapter',
        'info:eu-repo/semantics/review': 'other',
        'info:eu-repo/semantics/conferenceObject': 'proceedings-article',
        'info:eu-repo/semantics/lecture': 'other',
        'info:eu-repo/semantics/workingPaper': 'preprint',
        'info:eu-repo/semantics/preprint': 'preprint',
        'info:eu-repo/semantics/report': 'report',
        'info:eu-repo/semantics/annotation': 'dataset',
        'info:eu-repo/semantics/contributionToPeriodical': 'other',
        'info:eu-repo/semantics/patent': 'other',
        'info:eu-repo/semantics/other': 'other',
        # BASE
        'typenorm:0000': 'other',  # text
        'typenorm:0001': 'journal-article',
        'typenorm:0002': 'book',
        'typenorm:0003': 'proceedings-article',
        'typenorm:0004': 'thesis',
        'typenorm:0005': 'other',  # review
        'typenorm:0101': 'other',  # audio
        'typenorm:0102': 'other',  # video
        'typenorm:0103': 'poster',  # image
        'typenorm:0104': 'poster',  # map
        'typenorm:0105': 'other',  # software
        'typenorm:0106': 'dataset',
        'typenorm:0107': 'other',  # sheet music
        'typenorm:9999': 'other',  # unknown
        # RG
        'inProceedings': 'proceedings-article',
        }

SET_TO_PUBTYPE = {
        # HAL:
        'type:ART': 'journal-article',
        'type:COMM': 'proceedings-article',
        'type:COUV': 'book-chapter',
        'type:DOUV': 'proceedings',
        'type:HDR': 'thesis',
        'type:IMG': 'other',
        'type:LECTURE': 'other',
        'type:MAP': 'other',
        'type:OTHER': 'other',
        'type:OUV': 'book',
        'type:PATENT': 'other',
        'type:POSTER': 'poster',
        'type:REPORT': 'report',
        'type:SON': 'other',
        'type:THESE': 'thesis',
        'type:UNDEFINED': 'other',
        'type:VIDEO': 'other',

        }

# By default, pubtype is kept identical
CROSSREF_PUBTYPE_ALIASES = {
        'article': 'journal-article',
        }


