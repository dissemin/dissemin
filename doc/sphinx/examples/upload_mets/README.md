# Mets Examples

A collection of metadata how Dissemin creates them. Dissemin creates a METS container, the containing files are always named `mets.xml` and `document.pdf`.

# Installation

The script uses Python 3. Make sure to be in folder `mets-examples`, then execute

    python3 -m venv env
    source env/bin/activate
    pip install -r requirements.txt

This creates a virtual environment.

# Configuration

You can (must) set parameters in `settings.py`


# Invocation

Make sure to activate your virtual environment

    source env/bin/activate

Uploading is simple

    python upload.py <file.xml>

The script creates from the given METS XML document and `document.pdf` a METS container `mets.zip`.

Das Skript erzeugt aus der vorhandenen METS XML und `document.pdf` einen METS Container mets.zip. The file `document.pdf` ist a empty page.
