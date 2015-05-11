import ldap

conn = ldap.open('annuaire.ens.fr')

## The next lines will also need to be changed to support your search requirements and directory
baseDN = "ou=people, dc=ens, dc=fr"
searchScope = ldap.SCOPE_SUBTREE
## retrieve all attributes - again adjust to your needs - see documentation for more options
retrieveAttributes = None 
searchFilter = "cn=*farge*"

try:
	ldap_result_id = conn.search(baseDN, searchScope, searchFilter, retrieveAttributes)
	result_set = []
	while 1:
                print "Retry"
		result_type, result_data = conn.result(ldap_result_id, 0)
		if (result_data == []):
			break
		else:
			## here you don't have to append to a list
			## you could do whatever you want with the individual entry
			## The appending to list is just for illustration. 
			if result_type == ldap.RES_SEARCH_ENTRY:
				result_set.append(result_data)
	print result_set
except ldap.LDAPError, e:
	print e

print result_data

