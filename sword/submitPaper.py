import httplib
from zipfile import *
from lxml import etree
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
	conn.putheader("X-Packaging","http://purl.org/net/sword-types/AOfr")
	conn.putheader("Content-Type","application/zip")
	conn.putheader("Content-Disposition"," attachment; filename=meta.xml")
	conn.putheader("Content-Length",len(strData))
	conn.endheaders()
	conn.send(strData)
	r1 = conn.getresponse()
	print r1.read()

def _add_elem(initTree, tagName, text, attrib ={}):
"""_add_elem(tagName, text, attrib={})
Adds a child element in the appropriate place in the tree.
Raises an IndexError if the checker does not allow an addition child of tagName.
"""
	last_child = None
	for child in initTree._elem.findall('.//%s' % tagName):
		last_child = child
		if last_child is None:
			new_child = ET.SubElement(initTree._elem, tagName, attrib)
		else:
			new_child = ET.Element(tagName, attrib)
			self._elem.insert(initTree._elem._children.index(last_child)+1, new_child)
			new_child.text=str(text)
	return new_child 


#I will assume that the online "edition" is where I want
def UpdateHal(pdf,url):
	metadata  
	metadata = etree.fromstring(metata)
	nodeInteresting = metadata.find(".//edition") 
	etree.SubElement(nodeInteresting, 'ref', type="file", target="article.pdf")  	
	metadata = etree.tostring(metadata) 
	strData = CreateZipFromPdfAndMetadata(pdf,metadata)
	conn.putrequest("PUT", "/sword/"+idHal, True,True)
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

# edition editionStmt biblFull  listBibl body text tei

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
