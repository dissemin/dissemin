dissemin
================

Web platform showing the articles written by researchers of an institution.
It highlights the articles that are not freely available while uploading them would comply with the publisher's policy.

Data sources:
* OAI-PMH, through a proxy
* CrossRef.org
* SHERPA/RoMEO
* Soon: Bielefeld Academic Search Engine (BASE)

Dependencies:
* Python 2.7 (should work with Python 3)
* Django
* PyOAI

To use the RoMEO backend, it is useful to use a free api key. Write your api key in
the file `romeo_api_key` at the root of the repository so that dissemin can use it.

