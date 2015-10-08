import httplib2
from zipfile import *
from lxml import etree
from django import forms

import StringIO
import sword.metadataFormatter

#UPDATE NEEDED : IT seems that they change the doc, it is not with an host.
## simple wrapper function to encode the username & pass
def encodeUserData(user, password):
    return "Basic " + (user + ":" + password).encode("base64").rstrip()

u='dissemin'
p='disseminonhal'

conn = httplib2.Http("api-preprod.archives-ouvertes.fr")

httplib2.Http.debuglevel = 1 #Uncomment to debug mode


#TODO add specific headers for export-toarxiv and so one
#DOC in french on api-preprod.archives-ouvertes.fr

#TODO Abstract on the connection
def CreateZipFromPdfAndMetadata(pdf,metadata):
    s = StringIO.StringIO()
    with ZipFile(s,'w') as myZip:
        myZip.writestr("article.pdf",pdf) 
        myZip.writestr("meta.xml",metadata)
        myZip.close()
        return s.getvalue()



def MetadataHal(strData):  #Homemade sword protocol 
#TODO refactorize the code, fold on the headers
    conn.putrequest("POST", "/sword/hal/", True,True)
    conn.putheader("Authorization",encodeUserData(u,p))
    conn.putheader("Host","api-preprod.archives-ouvertes.fr")
    conn.putheader("X-Packaging","http://purl.org/net/sword-types/AOfr")
    conn.putheader("Content-Type","text/xml")
    conn.putheader("Content-Length",len(strData))
    conn.endheaders()
    conn.send(strData)
    r1 = conn.getresponse()
    print r1.read()


def FullHal(pdf,metadata):
    strData = CreateZipFromPdfAndMetadata(pdf,metadata)
    conn.putrequest("POST", "/sword/hal/", True,True)
    conn.putheader("Authorization",encodeUserData(u,p))
    conn.putheader("User-Agent", "curl/7.35.0")
    conn.putheader("Host","api-preprod.archives-ouvertes.fr")
    conn.putheader("Packaging","http://purl.org/net/sword-types/AOfr")
    conn.putheader("Content-Type","application/zip")
    conn.putheader("Content-Disposition"," attachment; filename=meta.xml")
    conn.putheader("Content-Length",len(strData))
    conn.endheaders()
    conn.send(strData)
    r1 = conn.getresponse()
    print r1.read()
#WARNING, ElementTree is not secure against malicious constructed data.
#I will assume that the online "edition" is where I want

def UpdateHal(pdf,idHal):
        strData = CreateZipFromPdfAndMetadata(pdf,sword.metadataFormatter.generate(4690))
        conn.putrequest("PUT", "/sword/"+idHal, True,True)
        conn.putheader("Host", "api-preprod.archives-ouvertes.fr")
        conn.putheader("Authorization",encodeUserData(u,p))
        conn.putheader("Packaging","http://purl.org/net/sword-types/AOfr")
        conn.putheader("Content-Type","application/zip")
        conn.putheader("Content-Disposition"," attachment; filename=meta.xml")
        conn.putheader("Content-Length",len(strData))
#        conn.putheader("Metadata-Relevant", "False")
        conn.endheaders()
        print "Sending... :\n"
        conn.send(strData)
        print "Sent :\n"
        r1 = conn.getresponse()
        print "Response :\n"
        print r1.read()

# edition editionStmt biblFull  listBibl body text tei
def bla():
    with open("sword/t/article.pdf","r") as art:
  		#FullHal(art.read(), sword.metadataFormatter.generate())      
			UpdateHal(art.read(),"inria-00528632")

#TODO parse the XML to search "<edition>" then add the src
#TODO Full SSL. Right now user/pass are not crypted.
#TODO new version file on HAL
#TODO modification of metadata on HAL
#TODO remove a file on HAL
#TODO add support for multiple files

#curl -v -u bthom:dissemin api-preprod.archives-ouvertes.fr/sword/hal -H "X-Packaging:http://purl.org/net/sword-types/AOfr" -X POST -H "Content-Type:text/xml" -d @art.xml
#
#curl -v -u bthom:dissemin api-preprod.archives-ouvertes.fr/sword/hal/ -X POST -H "X-Packaging:http://purl.org/net/sword-types/AOfr" -H "Content-Type:application/zip" -H "Content-Disposition:attachment; filename=meta.xml" --data-binary @dep.zip
