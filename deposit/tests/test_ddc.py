import pytest

from deposit.models import DDC

class TestDDC():
    """
    This class groups tests related to DDC class
    There are 99 DDCs already available due migration deposit/migrations/0016_populate_ddc
    """
    
    @pytest.mark.django_db
    def test_str(self):
        """
        String output should be of form 000 name
        """
        dct = {
            0   : '000',
            10  : '010',
            110 : '110',
        }
        for i, j in dct.items():
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
