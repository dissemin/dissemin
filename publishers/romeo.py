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



from io import BytesIO

import dateutil.parser
import re
import requests.exceptions

from datetime import datetime
from django.conf import settings
from lxml import etree as ET
from lxml.html import fromstring
from papers.errors import MetadataSourceException
from papers.utils import kill_html
from papers.utils import nstrip
from papers.utils import remove_diacritics
from papers.utils import sanitize_html
from publishers.models import Journal
from publishers.models import Publisher
from publishers.models import PublisherCondition
from publishers.models import PublisherCopyrightLink
from publishers.models import PublisherRestrictionDetail

class RomeoAPI(object):

    def __init__(self, api_key=settings.ROMEO_API_KEY):
        self.base_url = 'http://www.sherpa.ac.uk/romeo/api29.php'
        self.api_key = api_key

    def perform_romeo_query(self, search_terms):
        search_terms = search_terms.copy()
        if self.api_key:
            search_terms['ak'] = self.api_key

        # Perform the query
        try:
            req = requests.get(self.base_url, params=search_terms, timeout=20)
        except requests.exceptions.RequestException as e:
            raise MetadataSourceException('Error while querying RoMEO.\n' +
                                          'URL was: '+self.base_url+'\n' +
                                          'Parameters were: '+str(search_terms)+'\n' +
                                          'Error is: '+str(e))

        # Parse it
        try:
            parser = ET.XMLParser(encoding='ISO-8859-1')
            root = ET.parse(BytesIO(req.content), parser)
        except ET.ParseError as e:
            raise MetadataSourceException('RoMEO returned an invalid XML response.\n' +
                                          'URL was: '+self.base_url+'\n' +
                                          'Parameters were: '+str(search_terms)+'\n' +
                                          'Error is: '+str(e))

        return root

    def fetch_journal(self, search_terms, matching_mode='exact'):
        """
        Fetch the journal data from RoMEO. Returns an Journal object.
        search_terms should be a dictionnary object containing at least one of these fields:
        """
        allowed_fields = ['issn', 'jtitle']
        terms = search_terms.copy()
        # Make the title HTML-safe before searching for it in the database or in
        # the API
        if 'jtitle' in terms:
            terms['jtitle'] = kill_html(terms['jtitle'])

        # Check the arguments
        if not all(key in allowed_fields for key in terms):
            raise ValueError('The search terms have to belong to '+str(allowed_fields) +
                             'but the dictionary I got is '+str(terms))

        # Remove diacritics (because it has to be sent in ASCII to ROMEO)
        for key in terms:
            terms[key] = remove_diacritics(terms[key])
            if len(terms[key]) > 256:
                return None

        # First check we don't have it already
        journal = Journal.find(issn=terms.get('issn'), title=terms.get('jtitle'))
        if journal:
            return journal

        # Perform the query
        if matching_mode != 'exact':
            terms['qtype'] = matching_mode
        root = self.perform_romeo_query(terms)

        # Find the matching journals (if any)
        journals = list(root.findall('./journals/journal'))

        if not journals:
            return None
        elif len(journals) > 1:
            print("Warning, "+str(len(journals))+" journals match the RoMEO request, " +
                  "defaulting to the first one")
            # TODO different behaviour: get the ISSN and try again.
        journal = journals[0]

        names = list(journal.findall('./jtitle'))
        if not names:
            raise MetadataSourceException('RoMEO returned a journal without title.\n' +
                                          'Terms were: '+str(terms))
        if len(names) > 1:
            print("Warning, "+str(len(names))+" names provided for one journal, " +
                  "defaulting to the first one")
        name = kill_html(names[0].text)

        issn = None
        try:
            issn = nstrip(journal.findall('./issn')[0].text)
        except (KeyError, IndexError):
            pass

        essn = None
        try:
            issn = nstrip(journal.findall('./essn')[0].text)
        except (KeyError, IndexError):
            pass

        # Now we may have additional info (ISSN from Romeo), so it's worth trying again in the model
        model_journal = journal
        if issn != terms.get('issn') or essn or name != terms.get('jtitle'):
            model_journal = Journal.find(issn=issn, essn=essn, title=name)
        if model_journal:
            return model_journal

        # Otherwise we need to find the publisher
        publishers = root.findall('./publishers/publisher')
        if not publishers:
            return None
        # TODO here we shouldn't default to the first one but look it up using the
        # <romeopub>
        publisher_desc = publishers[0]

        publisher = self.get_or_create_publisher(publisher_desc)

        result = Journal(title=name, issn=issn, essn=essn, publisher=publisher)
        result.save()
        return result


    def fetch_publisher(self, publisher_name):
        """
        Retrieve a publisher from the RoMEO API.
        """
        if publisher_name is None:
            return

        # Prepare the query
        search_terms = dict()
        search_terms['pub'] = remove_diacritics(publisher_name)
        search_terms['qtype'] = 'all'

        root = self.perform_romeo_query(search_terms)

        # Find the publisher
        publishers = root.findall('./publishers/publisher')
        if len(publishers) == 0:
            return
        elif len(publishers) > 1:
            search_terms['qtype'] = 'exact'
            root = self.perform_romeo_query(search_terms)
            publishers = root.findall('./publishers/publisher')
            if len(publishers) != 1:
                return

        publisher = self.get_or_create_publisher(publishers[0])
        return publisher

    def fetch_all_publishers(self, modified_since=None):
        """
        Fetches all the publishers from RoMEO, optionally modified
        since a given date.
        """
        search_terms = {'all':'yes'}
        if modified_since:
            if isinstance(modified_since, datetime):
                modified_since = modified_since.date()
            search_terms['pdate'] = modified_since.isoformat()
        root = self.perform_romeo_query(search_terms)
        publishers = root.findall('./publishers/publisher')
        for publisher in publishers:
            try:
                self.get_or_create_publisher(publisher)
            except MetadataSourceException as exception:
                print(exception)

    def fetch_all_journals(self):
        """
        Fetches all the journals from RoMEO.
        """
        r = requests.get('http://www.sherpa.ac.uk/downloads/journal-title-issns.php',
                         {'ak':self.api_key, 'format':'tsv'})
        # r.encoding = 'ISO-8859-1'
        headers = None
        lines = r.text.split('\n')
        for line in lines:
            if not line:
                continue
            fields = line.strip().split('\t')
            if headers is None:
                headers = fields
            elif len(fields) != 5:
                continue
            else:
                [title, issn, essn, romeo_id, _] = fields
                issn = issn or None
                essn = essn or None
                match = Journal.find(issn=issn, essn=essn, title=title)

                if match and match.publisher.romeo_id != romeo_id:
                    if re.match('\d+', match.publisher.romeo_id):
                        # This journal has changed publisher!
                        try:
                            correct_publisher = Publisher.objects.get(romeo_id=romeo_id)
                            match.change_publisher(correct_publisher)
                        except Publisher.DoesNotExist:
                            pass
                    else:
                        # The existing RoMEO id is buggy (imported from a previous version of the API)
                        # so we just update it
                        try:
                            correct_publisher = Publisher.objects.get(romeo_id=romeo_id)
                            correct_publisher.merge(match.publisher)
                            match.change_publisher(correct_publisher)
                        except Publisher.DoesNotExist:
                            match.publisher.romeo_id = romeo_id
                            match.publisher.save(update_fields=['romeo_id'])
                elif match is None:
                    try:
                        publisher = Publisher.objects.get(romeo_id=romeo_id)
                        journal = Journal(title=title, issn=issn, essn=essn, publisher=publisher)
                        journal.save()
                    except Publisher.DoesNotExist:
                        pass

    def get_romeo_latest_update_date(self):
        """
        Fetches the dates of the latest updates on the RoMEO service.
        This returns a dict: the dates can be accessed via the 'publishers' and 'journals'
        keys.
        """
        r = requests.get('http://www.sherpa.ac.uk/downloads/download-dates.php',
                         {'ak':self.api_key, 'format':'xml'})
        parser = ET.XMLParser(encoding='ISO-8859-1')
        root = ET.parse(BytesIO(r.content), parser)
        return {
            'publishers': self._get_romeo_date(root, './publisherspolicies/latestupdate'),
            'journals': self._get_romeo_date(root, './journals/latestupdate')
        }

    def fetch_updates(self):
        """
        Update the publishers and journals in the model,
        only fetching the publishers which have been updated since the last update.

        The first time this is run, this fetches everything from RoMEO.
        """
        # First, determine latest update date for publishers in the model
        latest_update_in_model = None
        latest_updates = list(Publisher.objects.filter(last_updated__isnull=False).order_by('-last_updated').values_list('last_updated', flat=True)[:1])
        if latest_updates:
            latest_update_in_model = latest_updates[0]

        # Second, fetch the date of RoMEO's own last update
        latest_update_in_romeo = self.get_romeo_latest_update_date()['publishers']

        if latest_update_in_model is None or latest_update_in_model < latest_update_in_romeo:
            self.fetch_all_publishers(latest_update_in_model)

        self.fetch_all_journals()

    def get_or_create_publisher(self, romeo_xml_description):
        """
        Retrieves from the model, or creates into the model,
        the publisher corresponding to the <publisher> description
        from RoMEO.

        If the data from RoMEO is more fresh than what we have
        in cache, we update our model.
        """
        xml = romeo_xml_description
        romeo_id = None
        try:
            romeo_id = xml.attrib['id']
        except KeyError:
            raise MetadataSourceException('RoMEO did not provide a publisher id.')

        romeo_parent_id = None
        try:
            romeo_parent_id = xml.attrib['parentid']
        except KeyError:
            pass

        name = None
        try:
            raw_name = xml.findall('./name')[0].text.strip()
            name = fromstring(kill_html(sanitize_html(raw_name))).text
        except (KeyError, IndexError, AttributeError):
            raise MetadataSourceException(
                'RoMEO did not provide the publisher\'s name.')

        alias = None
        try:
            alias = nstrip(xml.findall('./alias')[0].text)
            if alias:
                alias = fromstring(kill_html(sanitize_html(alias))).text
        except (KeyError, IndexError):
            pass

        last_update = self._get_romeo_date(xml, './dateupdated')

        # Check if we already have it.
        # Sadly the romeo_id is not unique (as publishers imported from doaj
        # all get the same id, so we have to use the name too).
        matches = None
        if re.match('\d+', romeo_id): # numeric ids are unambiguous
            matches = Publisher.objects.filter(romeo_id=romeo_id)
        elif alias:
            matches = Publisher.objects.filter(
                romeo_id=romeo_id, name__iexact=name, alias__iexact=alias)
        else:
            matches = Publisher.objects.filter(
                romeo_id=romeo_id, name__iexact=name, alias__isnull=True)
        if matches:
            first_match = matches[0]
            if first_match.last_updated is not None and first_match.last_updated >= last_update:
                return matches[0]

        # Otherwise, create it
        url = None
        try:
            url = nstrip(xml.findall('./homeurl')[0].text)
        except (KeyError, IndexError):
            pass

        preprint = None
        try:
            preprint = xml.findall('./preprints/prearchiving')[0].text.strip()
        except (KeyError, IndexError, AttributeError):
            raise MetadataSourceException(
                'RoMEO did not provide the preprint policy.')

        postprint = None
        try:
            postprint = xml.findall('./postprints/postarchiving')[0].text.strip()
        except (KeyError, IndexError, AttributeError):
            raise MetadataSourceException(
                'RoMEO did not provide the postprint policy.')

        pdfversion = None
        try:
            pdfversion = xml.findall('./pdfversion/pdfarchiving')[0].text.strip()
        except (KeyError, IndexError, AttributeError):
            raise MetadataSourceException(
                'RoMEO did not provide the pdf archiving policy.')

        # Compute OA status of the publisher
        status = 'UNK'

        if not matches:
            publisher = Publisher()
        else:
            publisher = matches[0]

        publisher.name = name
        publisher.alias = alias
        publisher.url = url
        publisher.preprint = preprint
        publisher.postprint = postprint
        publisher.pdfversion = pdfversion
        publisher.romeo_id = romeo_id
        publisher.romeo_parent_id = romeo_parent_id
        publisher.oa_status = status
        publisher.last_updated = last_update
        publisher.save()

        if matches:
            publisher.publishercopyrightlink_set.all().delete()
            publisher.publisherrestrictiondetail_set.all().delete()
            publisher.publishercondition_set.all().delete()

        # Add the conditions, restrictions, and copyright
        for restriction in xml.findall('./preprints/prerestrictions/prerestriction'):
            self.add_restriction(restriction, 'preprint', publisher)

        for restriction in xml.findall('./postprints/postrestrictions/postrestriction'):
            self.add_restriction(restriction, 'postprint', publisher)

        for restriction in xml.findall('./pdfversion/pdfrestrictions/pdfrestriction'):
            self.add_restriction(restriction, 'pdfversion', publisher)

        for condition in xml.findall('./conditions/condition'):
            if condition.text:
                c = PublisherCondition(publisher=publisher,
                                       text=condition.text.strip())
                c.save()

        # Update the publisher status
        publisher.oa_status = publisher.classify_oa_status()
        publisher.save(update_fields=['oa_status'])

        # TODO: if the OA status has changed, then we should update the journals and papers accordingly with the
        # adequate task

        for link in xml.findall('./copyrightlinks/copyrightlink'):
            text = None
            url = None
            texts = link.findall('./copyrightlinktext')
            if texts:
                text = nstrip(texts[0].text)
            urls = link.findall('./copyrightlinkurl')
            if urls:
                url = nstrip(urls[0].text)
            if url and text:
                cplink = PublisherCopyrightLink(
                    text=text, url=url[:1024], publisher=publisher)
                cplink.save()

        return publisher


    def add_restriction(self, xml, applies_to, publisher):
        """
        Creates a sharing restriction (SAD!) for a publisher
        """
        text = nstrip(xml.text)
        if text:
            r = PublisherRestrictionDetail(
                publisher=publisher, applies_to=applies_to, text=text)
            r.save()

    def _get_romeo_date(self, xml, xpath):
        """
        Given an xml element and an XPath expression, return the parsed
        date contained in that element.
        """
        element = xml.findall(xpath)
        if element and element[0].text:
            return dateutil.parser.parse(element[0].text.strip().replace(' ', 'T')+'Z')
