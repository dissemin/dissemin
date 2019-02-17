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



from lxml import etree

XMLLANG_ATTRIB = '{http://www.w3.org/XML/1998/namespace}lang'


class MetadataFormatter(object):
    """
    Abstract interface formatting metadata to a SWORD format
    """

    def formatName(self):
        """
        A string, identifier for the format
        """
        return None

    def render(self, paper, filename, form=None):
        """
        Returns an XML node representing the article in the expected format
        The filename of the attached PDF should be None when uploading metadata only.
        """
        return None

    def toString(self, paper, filename, form=None, pretty=False,
                xml_declaration=True):
        """
        The metadata as a string
        """
        return etree.tostring(self.render(paper, filename, form),
                              pretty_print=pretty,
                              encoding='UTF-8',
                              xml_declaration=xml_declaration)


def addChild(elem, childName, text=None):
    """
    Utility function: create a node, append it and return it
    """
    node = etree.Element(childName)
    elem.append(node)
    if text is not None:
        node.text = text
    return node



