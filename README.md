dissemin
================

OAI-PMH harvester, restricting results to the employees of an institution.
The results are exposed as a web platform.

It discovers article through CrossRef.org.
It should include data from SHERPA/RoMEO soon.

Dependencies:
* Python 2.7 (should work with Python 3)
* Django
* PyOAI

To use the RoMEO backend, it is useful to use a free api key. Write your api key in
the file `romeo_api_key` at the root of the repository so that dissemin can use it.

