import httplib


## simple wrapper function to encode the username & pass
def encodeUserData(user, password):
    return "Basic " + (user + ":" + password).encode("base64").rstrip()

u='bthom'
p='dissemin'
conn = httplib.HTTPConnection("api-preprod.archives-ouvertes.fr")

#httplib.HTTPConnection.debuglevel = 1 #Uncomment to debug mode


def CreateMetadataHal(fl):  #Homemade sword protocol 
	with open(fl,"r") as data:
		strData = data.read()#.replace("\n","").replace("\t","").replace("\r","")
		conn.putrequest("POST", "/sword/hal/", True,True)
		conn.putheader("Authorization",encodeUserData(u,p))
		conn.putheader("Host","api-preprod.archives-ouvertes.fr")
#		conn.putheader("Accept","*/*")  #useless
		conn.putheader("X-Packaging","http://purl.org/net/sword-types/AOfr")
		conn.putheader("Content-Type","text/xml")
		conn.putheader("Content-Length",len(strData))
		conn.endheaders()
		conn.send(strData)
		r1 = conn.getresponse()
		print r1.read()


CreatemetadataHal("art.xml")
##curl -v -u bthom:dissemin api-preprod.archives-ouvertes.fr/sword/hal -H "X-Packaging:http://purl.org/net/sword-types/AOfr" -X POST -H "Content-Type:text/xml" -d @art.xml
