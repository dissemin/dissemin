import io
import logging
import os
import sys

from copy import copy
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm

from reportlab.platypus import Paragraph

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from reportlab.pdfgen import canvas

from django.conf import settings

logger = logging.getLogger('dissemin.' + __name__)

# Get the current module name to load functions by name
current_module = sys.modules[__name__]

# The dict contains the available functions and an admin-friendly name
REGISTERED_DECLARATION_FUNCTIONS = {
    'declaration_ulb_darmstadt' : 'ULB Darmstadt',
}


def get_declaration_pdf(deposit_record, user):
    """
    This function creates for a given deposit the letter of declaration. If this does not succeed, it raises an exception.
    :param deposit: DepositRecord containing information for declaration
    :returns: BytesIO containing pdf or raises Exception
    """
    declaration_name = deposit_record.repository.letter_declaration
    pdf_io = REGISTERED_DECLARATION_FUNCTIONS[declaration_name](deposit_record, user)
    return pdf_io


def declaration_ulb_darmstadt(deposit_record, user):
    """
    Takes a deposit and creates authors declaration for ULB Darmstadt and returns that.
    This function follows the corporate design of TUDA.
    As this is my (Stefans) first approach with reportlab, the way thingys are placed is not really good
    """

    pdf_buffer = io.BytesIO()

    page_width, page_height = A4
    
    font_path = os.path.join(settings.BASE_DIR, 'deposit', 'declarations', 'fonts')

    pdfmetrics.registerFont(TTFont("Charter Regular", os.path.join(font_path, 'Charter-Regular.ttf')))
    pdfmetrics.registerFont(TTFont("Front Page Regular", os.path.join(font_path, 'FrontPage-Pro-Regular.ttf')))
    
    logo_path = os.path.join(settings.BASE_DIR, 'deposit', 'declarations', 'logos')
    tu_logo = os.path.join(logo_path, 'tud_logo.png')
    ulb_logo = os.path.join(logo_path, 'tud_ulb_logo.png')

    # Create paragraph styles
    style_text = ParagraphStyle(
        name='ulb-text',
        fontName='Charter Regular',
        fontSize=10,
        leading=12,
    )
    style_text_center = copy(style_text)
    style_text_center.alignment = 2
    style_subject = ParagraphStyle(
        name='ulb-subject',
        fontName='Front Page Regular',
        fontSize=18,
        leading=21.6,
    )
    
    # Create the canvas
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    c.setTitle('Erklärung zur Publikation elektronischer Dokumente - {}'.format(deposit_record.paper.title))
    c.setAuthor('Universitäts- und Landesbibliothek Darmstadt, Team Digitales Publizieren')

    # Green bar
    c.setFillColor(tuple([i/255 for i in [0, 157, 129]]))
    c.rect(15*mm, page_height-20*mm, page_width-30*mm, 4*mm, fill=True, stroke=False)
    # Black line
    c.setFillColor((0, 0, 0))
    c.rect(15*mm, page_height-21.4*mm, page_width-30*mm, 1.2, fill=True, stroke=False)

    # The logos
    c.drawInlineImage(tu_logo, 147.3*mm, page_height-47.4*mm, height=22*mm, width=55*mm)
    c.drawInlineImage(ulb_logo, 173.3*mm, page_height-69.4*mm, height=22*mm, width=21.8*mm)

    # Address
    # The address is aligned with ULB-logo.
    # Since its anchor is bottom left, we have to move its height down
    address_text = """Universitäts- und Landesbibliothek Darmstadt<br/>
    Team Digitales Publizieren<br/>
    Magdalendenstraße 8<br/>
    64289 Darmstadt
    """
    available_width = 100*mm
    available_height = 22*mm

    address_p = Paragraph(address_text, style_text)
    used_width, used_height = address_p.wrap(available_width, available_height)
    address_p.drawOn(c, 15*mm, page_height - 48.4*mm - used_height)

    # Subject
    subject_text = """
    Erklärung zur Publikation elektronischer Dokumente
    <br/>
    (Autoren- und Herausgebervertrag)
    """
    available_width = page_width - 30*mm
    available_height = 30
    subject_p = Paragraph(subject_text, style_subject)
    used_width, used_height = subject_p.wrap(available_width, available_height)
    subject_p.drawOn(c, 15*mm, page_height - 74.4*mm - used_height)

    # Main text of the declaration. It's top is going the an arbitrary set point and the remaining height for dynamic generated content is referenced to this point
    available_width = page_width - 30*mm
    available_height = page_height - 20*mm - 95*mm

    main_text = """
    Hiermit gestatte ich (im folgenden: Autorin/Autor bzw. Herausgeberin/Herausgeber) der Universitäts- und Landesbibliothek (ULB) Darmstadt, das unten aufgeführte Werk bzw. dessen Teile in elektronischer Form zu den nachfolgend genannten Bedingungen zu publizieren und zur freien Nutzung im Internet anzubieten. Das Einverständnis der Autorinnen und Autoren dazu liegt vor.
    <br/>
    <br/>
    Die Autorin/der Autor bzw. die Herausgeberin/der Herausgeber versichert, dass sie/er berechtigt ist, über die urheberrechtlichen Nutzungsrechte an diesem Werk zu verfügen und dass bisher keine entgegenstehenden Verfügungen getroffen wurde. Sie/er erklärt, dass mit der Veröffentlichung des Werks keine Rechte Dritter verletzt werden und stellt die ULB Darmstadt von etwaigen Ansprüchen Dritter frei.
    <br/>
    <br/>
    Insbesondere gewährt die Autorin/der Autor bzw. die Herausgeberin/der Herausgeber der ULB Darmstadt das Recht,
    <br/>
    <br/>
    """
    
    main_p = Paragraph(main_text, style_text)
    used_width, used_height = main_p.wrap(available_width, available_height)
    available_height -= used_height
    start_height = page_height - 95*mm - used_height
    main_p.drawOn(c, 15*mm, start_height)

    # Some conditions as numbered list
    numbered_list = [
        'das Werk auf ihren eigenen Servern zu vervielfältigen und zu speichern sowie über die internationalen Datennetze zugänglich zu machen,',
        'das Werk an die Deutsche Nationalbibliothek sowie an bibliothekarische Partnereinrichtungen weiterzugeben, die ebenfalls zur dauerhaften Speicherung berechtigt sind,',
        'das Werk in andere Formate zu migrieren, sofern dies zur Nutzung oder Archivierung notwendig ist,',
        'die Metadaten frei an Datenbanken oder Verzeichnisse weiterzugeben.'
    ]

    # shall take 10mm
    available_width_number = 10*mm
    for idx, item_text in enumerate(numbered_list):
        # First the number
        number_p = Paragraph('(' + str(idx + 1) + ')', style_text)
        used_width, used_height = number_p.wrap(available_width_number, available_height)
        number_p.drawOn(c, 15*mm, start_height - used_height)
        
        # Then the text. We reduce the width accordingly
        item_p = Paragraph(item_text, style_text)
        used_width, used_height = item_p.wrap(available_width - available_width_number, available_height)
        available_height -= used_height
        start_height -= used_height
        item_p.drawOn(c, 25*mm, start_height)


    # The choosen license
    license_text = """
    <br/>
    Das Werk soll zusätzlich unter folgender Lizenz stehen:
    <br/>
    <br/>
    {}
    """.format(deposit_record.license.name)

    license_p = Paragraph(license_text, style_text)
    used_width, used_height = license_p.wrap(available_width, available_height)
    available_height -= used_height
    start_height -= used_height
    license_p.drawOn(c, 15*mm, start_height)
    
    # Next we do title, authors list
    # Finally the section for signing
    # If all this does not fit on this page, do it on the next
    # In theory, this could be not enough space, but I assume this must be > 200 authors or so

    title = deposit_record.paper.title # max 1024 Chars

    authors_list = ", ".join([str(author) for author in deposit_record.paper.authors])

    tuprints_id = deposit_record.identifier

    signer = user.first_name + ' ' + user.last_name

    work_text = """
    <br/>
    Titel des Werks: {}
    <br/><br/>
    Autor/innen: {}
    <br/><br/>
    TUPrints-ID (nach Veröffentlichung): {}
    """.format(title, authors_list, tuprints_id)

    work_text_p = Paragraph(work_text, style_text)
    used_width, used_height = work_text_p.wrap(available_width, available_height)
    available_height -= used_height
    start_height -= used_height
    work_text_p.drawOn(c, 15*mm, start_height)

    # Location, Date and a line for signing
    # We set location to Darmstadt and take the current date

    signer_text = """
    Name der Autorin/des Autors bzw. der Herausgeberin/des Herausgebers:
    {}
    <br/><br/>
    """.format(signer)
    location_date_text = 'Darmstadt, {}'.format(date.today().strftime('%d.%m.%Y'))

    # We compute the heights beginning from bottom elements
    start_height = 20*mm
    sign_text = Paragraph('(Unterschrift)', style_text_center)
    used_width, used_height = sign_text.wrap(100*mm, available_height)
    sign_text.drawOn(c, page_width - 15*mm - used_width, start_height)
    c.rect(page_width - 15*mm - used_width, start_height, 100*mm, 0.5, fill=True, stroke=False)

    location_date_p = Paragraph(location_date_text, style_text)
    used_width, used_height = location_date_p.wrap(available_width, available_height)
    available_height -= used_height
    location_date_p.drawOn(c, 15*mm, start_height)

    signer_p = Paragraph(signer_text, style_text)
    start_height += used_height
    used_width, used_height = signer_p.wrap(available_width, available_height)
    available_height -= used_height
    signer_p.drawOn(c, 15*mm, start_height)

    # We like to monitor the available height, to figure out if a second page is necessary
    # If the remaining height is < 0, we send error to sentry
    if available_height < 0:
        logger.error("While creating letter for ULB Darmstadt, height left was smaller than 0, leading to overlapping text. Deposit Record: {}".format(deposit_record.pk))

    # Finally make page, save and return the BytesIO
    c.showPage()
    c.save()
    return pdf_buffer


REGISTERED_DECLARATION_FUNCTIONS = {
        'ULB Darmstadt' : declaration_ulb_darmstadt,
}
