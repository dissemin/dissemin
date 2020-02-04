import io
import logging
import os
import subprocess

from datetime import date
from fdfgen import forge_fdf
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.utils.formats import date_format

from deposit.models import UserPreferences
from papers.models import Researcher


logger = logging.getLogger('dissemin.' + __name__)

PDF_TEMPLATE_DIR = os.path.join(settings.BASE_DIR, 'deposit', 'declarations', 'pdf_templates')

def get_declaration_pdf(deposit_record):
    """
    This function creates for a given deposit the letter of declaration. If this does not succeed, it raises an exception.
    :param deposit: DepositRecord containing information for declaration
    :returns: BytesIO containing pdf or raises Exception
    """
    declaration_name = deposit_record.repository.letter_declaration.function_key
    pdf_io = REGISTERED_DECLARATION_FUNCTIONS[declaration_name](deposit_record)
    return pdf_io


def fill_forms(pdf_path, fields, flatten=True):
    """
    Call this to fill in the form values into the document
    :param pdf_path: Path to the pdf that will be filled in
    :param fields: list of (Field name, Value) to be used to fill the form
    :param flatten: Set to false if you want to keep the forms
    :returns: PDF as IO
    """
    fdf = forge_fdf("",fields,[],[],[])

    # We cannot use /tmp, because on ubuntu, pdftk is delivered with snap
    # snap has no access to /tmp
    tmp_dir = os.path.join(settings.BASE_DIR, 'deposit', 'tmp', 'declarations')
    try:
        os.makedirs(tmp_dir)
    except OSError as e:
        logger.debug(e)

    with NamedTemporaryFile(mode='wb', delete=False, dir=tmp_dir) as fdf_file:
        fdf_file.write(fdf)

    with NamedTemporaryFile(delete=False, dir=tmp_dir, suffix='.pdf') as pdf_file:
        pass

    # Call the conversion
    command = ['pdftk', pdf_path, 'fill_form', fdf_file.name, 'output', pdf_file.name]
    if flatten:
        command.append('flatten')

    subprocess.run(command)

    # Get the pdf as BytesIO
    with open(pdf_file.name, 'rb') as f:
        pdf = io.BytesIO(f.read())

    # Clean temp files
    try:
        os.remove(fdf_file.name)
        os.remove(pdf_file.name)
    except Exception as e:
        logger.exception(e)

    return pdf


def declaration_ulb_darmstadt(deposit_record):
    """
    Creates the letter of declaration for TUprints (Tuprints contract) with fdfgen
    :param deposit_record: A deposit record
    :return: PDF as BytesIO.
    """

    user = deposit_record.user
    r = Researcher.objects.get(user=user)
    try:
        up = UserPreferences.objects.get(user=user)
    except UserPreferences.DoesNotExist:
        email = ''
    else:
        email = up.email or ''

    date_localized = date_format(date.today(), format='SHORT_DATE_FORMAT', use_l10n=True)

    fields = [
        ('Name Vorname Autor_in/Herausgeber_in', '{}, {}'.format(user.last_name, user.first_name)),
        ('ORCID Autor_in/Herausgeber_in', r.orcid or ''),
        ('EMail Autor_in/Herausgeber_in', email),
        ('Dissemin', 'Ja'),
        ('Ort Datum Autor_in/Herausgeber_in', 'Darmstadt, {}'.format(date_localized)),
    ]

    pdf_path = os.path.join(PDF_TEMPLATE_DIR, 'darmstadt_ulb.pdf')

    pdf_io = fill_forms(pdf_path, fields, flatten=False)

    return pdf_io

REGISTERED_DECLARATION_FUNCTIONS = {
        'ULB Darmstadt' : declaration_ulb_darmstadt,
}
