# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from urllib2 import urlopen, build_opener, URLError, Request
from urllib import urlencode
from random import randint
import json

translation_server_timeout = 10 # seconds
translation_server_url = 'http://localhost:1969/web'

redirect_resolver_user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:31.0) Gecko/20100101 Firefox/31.0 Iceweasel/31.1.0'

def check_full_text_availability(url):
    """
    Check using Zotero's translation-server if the full text is available at a given URL
    """
    available = None
    pdfurl = None
    opener = build_opener()
    try:
        # Get the final URL after the redirects
        req = Request(url, headers={'User-Agent:': redirect_resolver_user_agent})
        urlf = opener.open(req)
        new_url = urlf.geturl()
    except URLError as e:
        print "Failed to retrieve URL: "+url
        print "Error: "+unicode(e)
        return None

    try:
        # Generate a random sessionid
        sessionid = str(randint(1000,1000000))

        # Send it to the translation-server
        postdata = {'url':new_url,'sessionid':sessionid}
        req = Request(translation_server_url, data=json.dumps(postdata), headers={'Content-Type': 'application/json'})
        response = opener.open(req).read()
        
        # Read JSON output and find a PDF in it.
        parsed = json.loads(response)
        
        # For each "item" record
        found = False
        for item in parsed:
            attachments = item.get('attachments', [])
            for att in attachments:
                mime = att.get('mimeType', '')
                if mime == 'application/pdf':
                    found = True
                    pdfurl = att.get('url', None)
                    break
            if found:
                break

        available = found

    except HTTPError as e:
        if e.code == 300:
            # Multiple choices !
            # TODO use HTTPErrorProcessor to fetch the body of the 300 response, to see the choices
            # then iterate over these choices.
            print "Multiple choices are not implemented yet."
            return False
        else:
            print "Error from translation-server:"
            print unicode(e)
    except URLError as e:
        print "Failed to connect to translation-server:"
        print "Error: "+unicode(e)
        pass
    except ValueError as e:
        print "translation-server returned an invalid JSON output for "+url
        print "Error: "+unicode(e)

    return available
