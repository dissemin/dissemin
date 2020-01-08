import os
import sys
import requests

from io import BytesIO
from zipfile import ZipFile

from settings import deposit_url, packaging, auth

if len(sys.argv) != 2:
    sys.exit("Expecting exactly one file.")

# Set some paths
BASE_DIR = os.path.dirname(__file__)
PDF_FILE = os.path.join(BASE_DIR, 'document.pdf')

# Read xml from given file
with open(os.path.join(BASE_DIR, sys.argv[1])) as fin:
    mets = fin.read()

# Create zipfile in memory
payload = BytesIO()
with ZipFile(payload, 'w') as zipfile:
    zipfile.write(PDF_FILE, 'document.pdf')
    zipfile.writestr('mets.xml', mets)

# Prepare headers
headers = {
    'Content-type': 'application/zip',
    'Packaging': packaging,
    'Content-Disposition': 'filename=mets.zip',
}

r = requests.post(
    url=deposit_url,
    auth=auth,
    headers=headers,
    data=payload.getvalue(),
    timeout=10
)

# Print some information on deposit
print(r.status_code)
print(r.text)
