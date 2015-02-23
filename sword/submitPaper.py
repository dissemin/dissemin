import httplib
from zipfile import *
import StringIO
import sword.metadataFormatter
## simple wrapper function to encode the username & pass
def encodeUserData(user, password):
    return "Basic " + (user + ":" + password).encode("base64").rstrip()

u='bthom'
p='dissemin'
conn = httplib.HTTPConnection("api-preprod.archives-ouvertes.fr")

#httplib.HTTPConnection.debuglevel = 1 #Uncomment to debug mode


#TODO add specific headers for export-toarxiv and so one
#DOC in french on api-preprod.archives-ouvertes.fr

#TODO Abstract on the connection


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


def CreateZipFromPdfAndMetadata(pdf,metadata):
	s = StringIO.StringIO()
	with ZipFile(s,'w') as myZip:
		myZip.writestr("article.pdf",pdf) 
		myZip.writestr("meta.xml",metadata)
		myZip.close()
		return s.getvalue()



def FullHal(pdf,metadata):
	strData = CreateZipFromPdfAndMetadata(pdf,metadata)
	conn.putrequest("POST", "/sword/hal/", True,True)
	conn.putheader("Authorization",encodeUserData(u,p))
	conn.putheader("User-Agent", "curl/7.35.0")
	conn.putheader("Host","api-preprod.archives-ouvertes.fr")
	conn.putheader("X-Packaging","http://purl.org/net/sword-types/AOfr")
	conn.putheader("Content-Type","application/zip")
	conn.putheader("Content-Disposition"," attachment; filename=meta.xml")
	conn.putheader("Content-Length",len(strData))
	conn.endheaders()
	conn.send(strData)
	r1 = conn.getresponse()
	print r1.read()

with open("sword/article.pdf","r") as art:
 		FullHal(art.read(),sword.metadataFormatter.generate())

#TODO parse the XML to search "<edition>" then add the src
#TODO Full SSL. Right now user/pass are not crypted.
#TODO new version file on HAL
#TODO modification of metadata on HAL
#TODO remove a file on HAL
#TODO add support for multiple files

#curl -v -u bthom:dissemin api-preprod.archives-ouvertes.fr/sword/hal -H "X-Packaging:http://purl.org/net/sword-types/AOfr" -X POST -H "Content-Type:text/xml" -d @art.xml
#
#curl -v -u bthom:dissemin api-preprod.archives-ouvertes.fr/sword/hal/ -X POST -H "X-Packaging:http://purl.org/net/sword-types/AOfr" -H "Content-Type:application/zip" -H "Content-Disposition:attachment; filename=meta.xml" --data-binary @dep.zip
