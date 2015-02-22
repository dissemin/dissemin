from sword2 import *

#http://api-test.archives-ouvertes.fr/sword/
#test-ws test

c = Connection("http://api-preprod.archives-ouvertes.fr/sword/servicedocument",		user_name="bthom", user_pass="dissemin")

#c=Connection("http://127.0.0.1:1234/sd-uri", user_name="sword", user_pass="sword")
c.get_service_document()
print type(c)

collection = c.workspaces[0][1][0]
print collection.href
with open("art.xml","r") as data:
		receipt = c.create(col_iri="http://api-preprod.archives-ouvertes.fr/sword/hal",
									packaging = "http://purl.org/net/sword-types/AOfr",
									metadata_entry = data,									
									mimetype = "text/xml",
#							  	payload = data,
#									filename = "art.xml",
									)
	
#curl -v -u bthom:dissemin api-preprod.archives-ouvertes.fr/sword/hal -H "X-Packaging:http://purl.org/net/sword-types/AOfr" -X POST -H "Content-Type:text/xml" -d @art.xml
