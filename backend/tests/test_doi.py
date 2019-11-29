import pytest

from datetime import date

from backend.doi import CiteprocError
from backend.doi import CiteprocAuthorError
from backend.doi import CiteprocDateError
from backend.doi import CiteprocTitleError
from backend.doi import Citeproc
from backend.doi import CrossRef
from papers.baremodels import BareName


class TestCiteproc():
    """
    This class groups tests about the Citeproc class
    """

    test_class = Citeproc

    def test_to_paper_no_data(self):
        """
        If no data, must raise CiteprocError
        """
        with pytest.raises(CiteprocError):
            self.test_class.to_paper(None)


    def test_get_authors(self, citeproc):
        """
        The list of authors shall be a list of BareNames
        """
        r = self.test_class._get_authors(citeproc)
        assert isinstance(r, list)
        for barename in r:
            assert isinstance(barename, BareName)

    def test_get_authors_no_list(self, citeproc):
        """
        author in citeproc must be a list
        """
        del citeproc['author']
        with pytest.raises(CiteprocAuthorError):
            self.test_class._get_authors(citeproc)

    def test_get_authors_invalid_author(self, monkeypatch, citeproc):
        """
        If 'None' is an entry, raise exception
        """
        # We mock the function and let it return None, so that name_pairs is a list of None
        monkeypatch.setattr('backend.doi.convert_to_name_pair', lambda x: None)
        with pytest.raises(CiteprocAuthorError):
            self.test_class._get_authors(citeproc)


    def test_get_pubdate_issued(self, citeproc):
        """
        If contains issued, take this
        """
        citeproc['created'] = {'date-parts' : [2019, 10, 11]}
        citeproc['deposited'] = {'date-parts' : [2019, 10, 12]}
        assert self.test_class._get_pubdate(citeproc) == date(*citeproc['issued']['date-parts'])

    def test_get_pubdate_created(self, citeproc):
        """
        If contains no issued, take created
        """
        del citeproc['issued']
        citeproc['created'] = {'date-parts' : [2019, 10, 11]}
        citeproc['deposited'] = {'date-parts' : [2019, 10, 12]}
        assert self.test_class._get_pubdate(citeproc) == date(*citeproc['created']['date-parts'])

    def test_get_pubdate_deposited(self, citeproc):
        """
        If contains no issued and created, take deposited
        """
        del citeproc['issued']
        citeproc['deposited'] = {'date-parts' : [2019, 10, 12]}
        assert self.test_class._get_pubdate(citeproc) == date(*citeproc['deposited']['date-parts'])

    def test_get_pubdate_no_date(self, citeproc):
        """
        If contains no date, raise exception
        """
        del citeproc['issued']
        with pytest.raises(CiteprocDateError):
            self.test_class._get_pubdate(citeproc)

    def test_get_pubdate_received_none(self, monkeypatch):
        """
        If no valid date is found, raise exception
        """
        monkeypatch.setattr(self.test_class, '_parse_date', lambda x: None)
        with pytest.raises(CiteprocDateError):
            self.test_class._get_pubdate(dict())


    def test_get_title(self, citeproc):
        r = self.test_class._get_title(citeproc)
        assert r == citeproc['title']

    def test_get_title_no_title(self, citeproc):
        """
        Title is mandatory
        """
        del citeproc['title']
        with pytest.raises(CiteprocTitleError):
            self.test_class._get_title(citeproc)


    @pytest.mark.parametrize('data, expected', [({'date-parts' : [2019, 10, 10]}, date(2019, 10, 10)), ({'raw' : '2019-10-10'}, date(2019, 10, 10)), (None, None), ({'spam' : 'ham'}, None)])
    def test_parse_date(self, data, expected):
        """
        Must return a valid date or None
        """
        assert self.test_class._parse_date(data) == expected



    @pytest.mark.parametrize('date_parts, expected', [([2019, ], date(2019, 1, 1)), ([2019, 10, ], date(2019, 10, 1)), ([2019, 10, 10], date(2019, 10, 10))])
    def test_parse_date_parts(self, date_parts, expected):
        """
        Must parse the date list
        """
        assert self.test_class._parse_date_parts(date_parts) == expected




class TestCrossRef(TestCiteproc):
    """
    This class groups tests about the CrossRef class
    """

    test_class = CrossRef

    @pytest.fixture
    def citeproc(self, citeproc):
        """
        In general, the CrossRef is identical to citeproc, but there are some differences.
        We change the fixture accordingly
        """
        title = citeproc['title']
        citeproc['title'] = [title, ]

        return citeproc


    def test_get_title(self, citeproc):
        """
        CrossRef does serve the title in a list
        """
        r = self.test_class._get_title(citeproc)
        assert r == citeproc.get('title')[0]
    
    def test_get_title_list_error(self, citeproc):
        """
        CrossRef does serve the title in a list
        List must not be non-empty
        """
        citeproc['title'] = list()
        with pytest.raises(CiteprocTitleError):
            self.test_class._get_title(citeproc)
