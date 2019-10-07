import pytest

from deposit.tests.test_protocol import MetaTestProtocol


@pytest.mark.usefixtures('dark_archive_protocol')
class TestDarkArchiveProtocol(MetaTestProtocol):
    """
    A test class for named protocol
    """

    @pytest.mark.xfail
    def test_get_bound_form(self):
        pass

    @pytest.mark.xfail
    def test_protocol_registered(self):
        pass


    def test_str(self):
        """
        Tests the string output
        """
        s = self.protocol.__str__()
        assert isinstance(s, str) == True
