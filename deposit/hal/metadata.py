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

"""
This module defines a OAfr/TEI exporter, to be used with the SWORD interface to HAL.

"""

from __future__ import unicode_literals

from deposit.sword.metadata import addChild
from deposit.sword.metadata import MetadataFormatter
from lxml import etree
from django.utils.translation import ugettext as _

XMLLANG_ATTRIB = '{http://www.w3.org/XML/1998/namespace}lang'

HAL_TOPIC_CHOICES = [
    ('CHIM', _('Chemistry')),
    ('INFO', _('Computer science')),
    ('MATH', _('Mathematics')),
    ('PHYS', _('Physics')),
    ('NLIN', _('Non-linear science')),
    ('SCCO', _('Cognitive science')),
    ('SDE', _('Environment sciences')),
    ('SDU', _('Planet and Universe')),
    ('SHS.ANTHRO-BIO', _('Biological anthropology')),
    ('SHS.ANTHRO-SE', _('Social Anthropology and ethnology')),
    ('SHS.ARCHEO', _('Archaeology and Prehistory')),
    ('SHS.ARCHI', _('Architecture, space management')),
    ('SHS.ART', _('Art and art history')),
    ('SHS.CLASS', _('Classical studies')),
    ('SHS.DEMO', _('Demography')),
    ('SHS.DROIT', _('Law')),
    ('SHS.ECO', _('Economies and finances')),
    ('SHS.EDU', _('Education')),
    ('SHS.ENVIR', _('Environmental studies')),
    ('SHS.GENRE', _('Gender studies')),
    ('SHS.GEO', _('Geography')),
    ('SHS.GESTION', _('Business administration')),
    ('SHS.HISPHILSO', _('History, Philosophy and Sociology of Sciences')),
    ('SHS.HIST', _('History')),
    ('SHS.INFO', _('Library and information sciences')),
    ('SHS.LANGUE', _('Linguistics')),
    ('SHS.LITT', _('Literature')),
    ('SHS.MUSEO', _('Cultural heritage and museology')),
    ('SHS.MUSIQ', _('Musicology and performing arts')),
    ('SHS.PHIL', _('Philosophy')),
    ('SHS.PSY', _('Psychology')),
    ('SHS.RELIG', _('Religions')),
    ('SHS.SCIPO', _('Political science')),
    ('SHS.SOCIO', _('Sociology')),
    ('SHS.STAT', _('Methods and statistics')),
    ('SDV', _('Life sciences')),
    ('SPI', _('Engineering sciences')),
    ('STAT', _('Statistics')),
    ('QFIN', _('Economy and quantitative finance')),
  ]


def aofrDocumentType(paper):
    if all([not p.has_publication_metadata() for p in paper.oairecords]):
        return 'OTHER'
    tr = {
            'journal-article': 'ART',
            # (sinon les métadonnées sont énervantes avec ça:
            # bypass: 'proceedings-article': 'COUV',
            'proceedings-article': 'COMM',
            'book-chapter': 'COUV',
            'book': 'OUV',
            'proceedings': 'DOUV',
            'reference-entry': 'OTHER',
            'poster': 'POSTER',
            'report': 'REPORT',
            'thesis': 'THESE',
            'dataset': 'OTHER',
            'preprint': 'UNDEFINED',
            'other': 'OTHER',
         }
    return tr[paper.doctype]


class AOFRFormatter(MetadataFormatter):
    """
    Formatter for HAL
    """

    def formatName(self):
        return "AOfr"

    def render(self, paper, filename, form):
        xmlns_uri = 'http://www.tei-c.org/ns/1.0'
        xmlns = '{%s}' % xmlns_uri
        nsmap = {None: xmlns_uri, 'hal': 'http://hal.archives-ouvertes.fr'}
        tei = etree.Element(xmlns+'TEI', nsmap=nsmap)
        text = addChild(tei, 'text')
        body = addChild(text, 'body')
        listBibl = addChild(body, 'listBibl')
        biblFull = addChild(listBibl, 'biblFull')

        # titleStmt
        titleStmt = addChild(biblFull, 'titleStmt')

        self.renderTitleAuthors(titleStmt, paper,
                form.cleaned_data['affiliation'],
                form.cleaned_data['depositing_author'])

        # editionStmt
        if filename is not None:
            editionStmt = addChild(biblFull, 'editionStmt')
            edition = addChild(editionStmt, 'edition')
            date = addChild(edition, 'date')
            date.attrib['type'] = 'whenWritten'
            date.text = paper.pubdate.isoformat()
            ref = addChild(edition, 'ref')
            ref.attrib['type'] = 'file'
            ref.attrib['subtype'] = 'author'  # TODO adapt based on form info
            ref.attrib['target'] = filename

        # publicationStmt
        # publicationStmt = addChild(biblFull, 'publicationStmt')
        # TODO add license here

        # seriesStmt
        seriesStmt = addChild(biblFull, 'seriesStmt')
        idno = addChild(seriesStmt, 'idno')
        idno.attrib['type'] = 'stamp'
        idno.attrib['n'] = 'ENS-PARIS'
        # TODO add other stamps here (based on the institutions)

        halType = aofrDocumentType(paper)

        # notesStmt
        notesStmt = addChild(biblFull, 'notesStmt')
        note = addChild(notesStmt, 'note')
        note.attrib['type'] = 'popular'
        note.attrib['n'] = '0'
        note = addChild(notesStmt, 'note')
        note.attrib['type'] = 'audience'
        note.attrib['n'] = '2'
        note = addChild(notesStmt, 'note')
        note.attrib['type'] = 'peer'
        note.attrib['n'] = '1'

        if halType == 'COMM':
            note = addChild(notesStmt, 'note')
            note.attrib['type'] = 'invited'
            note.attrib['n'] = '0'
            note = addChild(notesStmt, 'note')
            note.attrib['type'] = 'proceedings'
            note.attrib['n'] = '1'

        if halType == 'OTHER':
            note = addChild(notesStmt, 'note')
            note.attrib['type'] = 'description'
            note.text = paper.doctype

        # sourceDesc
        sourceDesc = addChild(biblFull, 'sourceDesc')
        biblStruct = addChild(sourceDesc, 'biblStruct')
        analytic = addChild(biblStruct, 'analytic')

        self.renderTitleAuthors(analytic, paper,
                form.cleaned_data['affiliation'],
                form.cleaned_data['depositing_author'])

        for publication in paper.publications:
            date = publication.pubdate or paper.pubdate
            self.renderPubli(biblStruct, publication, halType, date)
            break # stop after the first publication

        if not paper.publications:
            # we still need to add an <imprint> for
            # the publication date
            monogr = addChild(biblStruct, 'monogr')
            imprint = addChild(monogr, 'imprint')
            data = addChild(imprint, 'date')
            data.attrib['type'] = 'datePub'
            data.text = paper.pubdate.isoformat()

        # profileDesc
        profileDesc = addChild(biblFull, 'profileDesc')
        langUsage = addChild(profileDesc, 'langUsage')
        language = addChild(langUsage, 'language')
        language.attrib['ident'] = 'en'  # TODO adapt this?
        textClass = addChild(profileDesc, 'textClass')

        keywords = addChild(textClass, 'keywords')
        keywords.attrib['scheme'] = 'author'
        term = addChild(keywords, 'term')
        term.attrib[XMLLANG_ATTRIB] = 'en'
        term.text = 'dissemin'

        domains = [form.cleaned_data['topic'].lower()]
        for domain in domains:
            classCode = addChild(textClass, 'classCode')
            classCode.attrib['scheme'] = 'halDomain'
            classCode.text = domain
        typology = addChild(textClass, 'classCode')
        typology.attrib['scheme'] = 'halTypology'
        typology.attrib['n'] = halType

        abstract = addChild(profileDesc, 'abstract')
        abstract.attrib[XMLLANG_ATTRIB] = 'en'
        abstract.text = 'No abstract.' if not form.cleaned_data[
            'abstract'] else form.cleaned_data['abstract']
        for record in paper.sorted_oai_records:
            if record.description:
                abstract.text = record.description
                break

        # back = addChild(text, 'back')

        return tei

    def renderTitleAuthors(self, root, paper,
            author_structure, depositing_id):
        """
        :param author_structure: the structure id of the depositing
            author
        :param depositing_id: the index of the depositing author
            in the list of authors
        """
        title = addChild(root, 'title')
        title.attrib[XMLLANG_ATTRIB] = 'en'  # TODO: autodetect language?
        title.text = paper.title

        for idx, author in enumerate(paper.authors):
            node = addChild(root, 'author')
            node.attrib['role'] = 'aut'
            nameNode = addChild(node, 'persName')

            name = author.name
            curtype = 'first'
            for first in name.first.split(' '):
                forename = addChild(nameNode, 'forename')
                forename.attrib['type'] = curtype
                forename.text = first
                curtype = 'middle'

            lastName = addChild(nameNode, 'surname')
            lastName.text = name.last

            if idx == depositing_id:
                affiliation = addChild(node, 'affiliation')
                affiliation.attrib['ref'] =('#struct-%s' %
                        unicode(author_structure))

    def renderPubli(self, biblStruct, publi, halType, pubdate):
        # TODO: handle publication type properly
        root = addChild(biblStruct, 'monogr')
        if publi.journal:
            self.renderJournal(root, publi.journal)

        title = addChild(root, 'title')
        if halType == 'COUV' or halType == 'OUV' or halType == 'COMM':
            title.attrib['level'] = 'm'
        else:
            title.attrib['level'] = 'j'
        title.text = publi.journal_title or publi.full_journal_title()

        # 'COMM' is disabled, use 'COUV' instead

        if halType == 'COMM':
            meeting = addChild(root, 'meeting')
            title = addChild(meeting, 'title')
            title.text = publi.journal_title or publi.full_journal_title()
            date = addChild(meeting, 'date')
            date.attrib['type'] = 'start'
            date.text = unicode(pubdate.year)
            settlement = addChild(meeting, 'settlement')
            settlement.text = '-'
            country = addChild(meeting, 'country')
            country.attrib['key'] = 'FR'

        imprint = addChild(root, 'imprint')

        if publi.publisher:
            publisher = addChild(imprint, 'publisher')
            publisher.text = unicode(publi.publisher)
        if publi.issue:
            biblScope = addChild(imprint, 'biblScope')
            biblScope.attrib['unit'] = 'issue'
            biblScope.text = publi.issue
        if publi.volume:
            biblScope = addChild(imprint, 'biblScope')
            biblScope.attrib['unit'] = 'volume'
            biblScope.text = publi.volume
        if publi.pages:
            biblScope = addChild(imprint, 'biblScope')
            biblScope.attrib['unit'] = 'pp'
            biblScope.text = publi.pages
        if publi.doi:
            idno = addChild(biblStruct, 'idno')
            idno.attrib['type'] = 'doi'
            idno.text = publi.doi

        data = addChild(imprint, 'date')
        data.attrib['type'] = 'datePub'
        data.text = pubdate.isoformat()

    def renderJournal(self, root, journal):
        pass


