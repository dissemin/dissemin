import io
import os
import pytest

from django.conf import settings

from deposit.declaration import declaration_ulb_darmstadt
from deposit.declaration import fill_forms
from deposit.models import License


class TestDeclarationLettersForms():
    """
    Class groups tests about generating the letter in general, not a specific one
    """

    @pytest.mark.parametrize('flatten', [True, False])
    def test_fill_forms(self, flatten):
        """
        Takes just a simple PDF to fill in and check if valid pdf
        """
        fields = [
            ('Textfeld 1', 'Eggs, bacon, spam and spam'),
            ('Markierfeld 1', True),
            ('Optionsfeld 1', True),
            ('Datumsfeld 1', '20.12.2019'),
            ('Numerisches Feld 1', '10'),
            ('RadioGroup1', True),
        ]
        pdf_path = os.path.join(settings.BASE_DIR, 'deposit', 'tests', 'data', 'declaration', 'sample.pdf')
        pdf = fill_forms(pdf_path, fields, flatten)
        assert isinstance(pdf, io.BytesIO)
        assert pdf.getbuffer().nbytes > 1


@pytest.mark.usefixtures('deposit_record')
class TestDeclarationLetters():
    """
    Class that groups test for generating letter of deposits.
    """
    def test_declaration_ulb_darmstadt(self):
        """
        This tests the letter of declaration for ULB Darmstadt.
        """
        self.dr.repository.save()

        self.client.user.first_name = 'Jose'
        self.client.user.last_name = 'Saramago'

        self.dr.license = License.objects.all().first()
        self.dr.identifier = '5732'
        self.dr.user = self.client.user
        self.dr.save()

        declaration_ulb_darmstadt(self.dr)
