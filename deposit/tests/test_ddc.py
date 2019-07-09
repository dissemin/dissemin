import pytest

from deposit.models import DDC

class TestDDC():
    """
    This class groups tests related to DDC class
    There are 99 DDCs already available due migration deposit/migrations/0016_populate_ddc
    """

    ddcs = {
            0   : '000',
            10  : '010',
            110 : '110',
    }

    
    @pytest.mark.django_db
    def test_str(self):
        """
        String output should be of form 000 name
        """
        for i, j in self.ddcs.items():
            d = DDC.objects.get(number=i)
            assert d.__str__() == j + " " + d.name

    @pytest.mark.django_db
    def test_ordering(self):
        """
        Make sure that the defined ordering applies
        """
        DDC.objects.create(number=1, name='Knowledge')
        ddcs = [ddc.number for ddc in DDC.objects.all()]
        assert all(ddcs[i] < ddcs[i+1] for i in range(1,len(ddcs)-1))

    @pytest.mark.django_db
    def test_number_as_string(self):
        """
        Should be always three digits.
        """
        for i in self.ddcs.keys():
            d = DDC.objects.get(number=i)
            assert len(d.number_as_string) == 3
