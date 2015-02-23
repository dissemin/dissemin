# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

from lxml import etree

from papers.models import Paper, Publication, Author, Researcher, Name, OaiRecord
from papers.utils import split_words

class MetadataFormatter(object):
    """
    Abstract interface formatting metadata to a SWORD format
    """

    def formatName(self):
        """
        A string, identifier for the format
        """
        return None
    
    def render(self, paper, filename):
        """
        Returns an XML node representing the article in the expected format
        The filename of the attached PDF should be None when uploading metadata only.
        """
        return None

    def toString(self, paper, filename, pretty=False):
        """
        The metadata as a string
        """
        return etree.tostring(self.render(paper, filename), pretty_print=pretty)

def addChild(elem, childName):
    """
    Utility function: create a node, append it and return it
    """
    node = etree.Element(childName)
    elem.append(node)
    return node

class AOFRFormatter(MetadataFormatter):
    """
    Formatter for HAL
    """

    def formatName(self):
        return "AOfr"

    def render(self, paper, filename):
        xmlns_uri = 'http://www.tei-c.org/ns/1.0'
        xmlns = '{%s}' % xmlns_uri
        nsmap = {None: xmlns_uri, 'hal':'http://hal.archives-ouvertes.fr'}
        tei = etree.Element(xmlns+'TEI', nsmap=nsmap)
        text = addChild(tei, 'text')
        body = addChild(text, 'body')
        listBibl = addChild(body, 'listBibl')
        biblFull = addChild(listBibl, 'biblFull')

        # titleStmt
        titleStmt = addChild(biblFull, 'titleStmt')

        self.renderTitleAuthors(titleStmt, paper)

        # editionStmt
        if filename != None:
            editionStmt = addChild(biblFull, 'editionStmt')
            edition = addChild(editionStmt, 'edition')
            ref = addChild(edition, 'ref')
            ref.attrib['type'] = 'file'
            ref.attrib['subtype'] = 'author'
            ref.attrib['target'] = filename

        # sourceDesc
        sourceDesc = addChild(biblFull, 'sourceDesc')
        biblStruct = addChild(sourceDesc, 'biblStruct')
        analytic = addChild(biblStruct, 'analytic')

        self.renderTitleAuthors(analytic, paper)

        for publication in paper.publication_set.all():
            self.renderPubli(biblStruct, publication)

        # profileDesc
        profileDesc = addChild(biblFull, 'profileDesc')
        textClass = addChild(profileDesc, 'textClass')
        langUsage = addChild(textClass, 'langUsage')
        language = addChild(langUsage, 'language')
        language.attrib['ident'] = 'en' # TODO adapt this?

        domains = ['spi.plasma', 'phys.phys.phys-gen-ph']
        for domain in domains:
            classCode = addChild(textClass, 'classCode')
            classCode.attrib['scheme'] = 'halDomain'
            classCode.text = domain
        typology = addChild(textClass, 'classCode')
        typology.attrib['scheme'] = 'halTypology'
        typology.attrib['n'] = 'ART' # TODO change this

        back = addChild(text, 'back')

        return tei

    def renderTitleAuthors(self, root, paper):
        title = addChild(root, 'title')
        # TODO this should be xml:lang
        title.attrib['lang'] = 'en' # TODO: autodetect language?
        title.text = paper.title
        
        for author in paper.sorted_authors:
            node = addChild(root, 'author')
            node.attrib['role'] = 'aut'
            nameNode = addChild(node, 'persName')

            name = author.name
            curtype = 'first'
            for first in split_words(name.first):
                forename = addChild(nameNode, 'forename')
                forename.attrib['type'] = curtype
                forename.text = first
                curtype = 'middle'

            lastName = addChild(nameNode, 'surname')
            lastName.text = name.last

    def renderPubli(self, biblStruct, publi):
        # TODO: handle publication type properly
        root = addChild(biblStruct, 'monogr')
        if publi.journal:
             self.renderJournal(root, publi.journal)

        title = addChild(root, 'title')
        title.attrib['level'] = 'j' # TODO: this should be adapted based on the type
        title.text = publi.full_title()

        imprint = addChild(root, 'imprint')
               
        if publi.publisher:
            publisher = addChild(imprint, 'publisher')
            publisher.text = publi.publisher
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

    def renderJournal(self, root, journal):
        pass



# The following lines are for testing purposes only
formatter = AOFRFormatter()
paper = Paper.objects.get(pk=1234)
print formatter.toString(paper, 'article.pdf', True)





