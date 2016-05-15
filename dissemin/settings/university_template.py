# coding: utf-8

### University names. ###
# This is used at various places to name the university.
# The URLs are not pointing to any special interface, they are only used
# to redirect users to the relevant websites.
UNIVERSITY_BRANDING = {
        u'UNIVERSITY_FULL_NAME': u'École Normale Supérieure',
        u'UNIVERSITY_SHORT_NAME': u"l'ENS",
        u'UNIVERSITY_SHORT_NAME_WITHOUT_DETERMINER': u"ENS",
        u'UNIVERSITY_REPOSITORY_URL': u'http://hal-ens.archives-ouvertes.fr/',
        u'UNIVERSITY_URL': u'http://www.ens.fr/',
}

### Central Authentication System ###
# This is used to authenticate your users.
# You only have to provide the URL of your CAS system and users
# will automatically be redirected to this page to log in from dissemin.
# Therefore no account creation is needed!
ENABLE_CAS = False # It will add the relevant middlewares and auth backends.
CAS_SERVER_URL="https://sso.ens.fr/cas/login"    #CRI CAS

# When logging out from dissemin, should we also log out from the CAS?
CAS_LOGOUT_COMPLETELY = True
# Should we provide a redirect URL to the CAS so that unlogged users
# can come back to dissemin?
CAS_PROVIDE_URL_TO_LOGOUT = True
