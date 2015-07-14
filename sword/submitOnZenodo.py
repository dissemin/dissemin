import json
import requests 
from os.path import basename
from dissemin.settings import ZENODO_KEY
#THIS IS PRIVATE


#url = "https://zenodo.org/api/deposit/depositions/1234/files?access_token=2SsQE9VkkgDQG1WDjrvrZqTJtkmsGHICEaccBY6iAEuBlSTdMC6QvcTR2HRv"
#TODO error handling

ZENODO_API_URL = "https://zenodo.org/api/deposit/depositions"

def submitPubli(paper,filePdf):
    if ZENODO_KEY is None:
        raise ValueError("No Zenodo API key provided.")

    # Checking the access token
    r = requests.get(ZENODO_API_URL+"?access_token=" + ZENODO_KEY)
    print(r.status_code)

    # Creating a new deposition
    headers = {"Content-Type": "application/json"}
    r = requests.post(ZENODO_API_URL+"?access_token=" + ZENODO_KEY , data="{}", headers=headers)
    print(r.status_code)
    deposition_id = r.json()['id']

    # Uploading the PDF
    data = {'filename':basename(filePdf)}
    files = {'file': open(filePdf, 'rb')}
    r = requests.post(ZENODO_API_URL+"/%s/files?access_token=%s" % (deposition_id,ZENODO_KEY), data=data, files=files)
    print(r.status_code)

    # Submitting the metadata
    abstract = "No abstract"
    for record in paper.sorted_oai_records:
        if record.description:
            abstract = record.description
            break
    data = {"metadata": {"title": paper.title,
                        "upload_type": "publication",
                        "publication_type": "conferencepaper",
                        "description": abstract,
                        "creators": map(lambda x:{"name": x.name.last +", " + x.name.first , "affiliation" : "ENS" }  ,paper.sorted_authors)}}
    for publi in paper.publication_set.all():
        if publi.pubdate:
            # TODO output more precise date if available
            data['metadata']['publication_date'] = str(publi.pubdate.year)+"-01-01"
            break
    for publi in paper.publication_set.all():
        if publi.doi:
            data['metadata']['doi']= publi.doi
            break
    r = requests.put(ZENODO_API_URL+"/%s?access_token=%s" % ( deposition_id, ZENODO_KEY), data=json.dumps(data), headers=headers)
    
    # Deleting the deposition
    print(r.status_code)
    r = requests.delete(ZENODO_API_URL+"/%s?access_token=%s" % ( deposition_id, ZENODO_KEY) )
#    r = requests.post("https://zenodo.org/api/deposit/depositions/%s/actions/publish?access_token=2SsQE9VkkgDQG1WDjrvrZqTJtkmsGHICEaccBY6iAEuBlSTdMC6QvcTR2HRv" % deposition_id)
#   print(r.status_code)
    return r
