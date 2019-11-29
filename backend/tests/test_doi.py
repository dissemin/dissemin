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


    @pytest.mark.parametrize('author_elem, expected', [(dict(), None), ({'affiliation' : [{'name' : 'Porto'}]}, 'Porto'), ({'affiliation' : [{'name' : 'Porto'}, {'name' : 'Lissabon'}]}, 'Porto')])
    def test_get_affiliation(self, author_elem, expected):
        """
        Must return the first affiliation if any
        """
        assert self.test_class._get_affiliation(author_elem) == expected


    def test_get_affiliations(self, affiliations, citeproc):
        """
        Must have the same length as citeproc['author'] and identical to list of affiliations
        """
        r = self.test_class._get_affiliations(citeproc)
        assert len(r) == len(citeproc.get('author'))
        assert r == affiliations

    def test_get_affiliations_no_authors(self, citeproc):
        """
        Must rais exception
        """
        del citeproc['author']
        with pytest.raises(CiteprocAuthorError):
            self.test_class._get_affiliations(citeproc)


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


    @pytest.mark.parametrize('orcid, expected', [({'ORCID' : '0000-0001-8187-9704'}, '0000-0001-8187-9704'), ({'ORCID' : '0000-0001-8187-9705'}, None), ({}, None)])
    def test_get_orcid(self, orcid, expected):
        """
        Must be valid or None
        """
        assert self.test_class._get_orcid(orcid) == expected

    def test_get_orcids(self, orcids, citeproc):
        """
        Must have the same length as citeproc['author'] and identical to list of  orcid
        """
        r = self.test_class._get_orcids(citeproc)
        assert len(r) == len(citeproc.get('author'))
        assert r == orcids

    def test_get_orcid_no_authors(self, citeproc):
        """
        Must rais exception
        """
        del citeproc['author']
        with pytest.raises(CiteprocAuthorError):
            self.test_class._get_orcids(citeproc)


    def test_get_paper_data(self, affiliations, orcids, title, citeproc):
        """
        We do some assertions on the results, but relatively lax, as we test the called functions, too
        """
        r = self.test_class._get_paper_data(citeproc)
        assert r['affiliations'] == affiliations
        for a in r['authors']:
            assert isinstance(a, BareName)
        assert r['orcids'] == orcids
        assert r['pubdate'] == date(*citeproc['issued']['date-parts'])
        assert r['title'] == title


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
    def citeproc(self, title, citeproc):
        """
        In general, the CrossRef is identical to citeproc, but there are some differences.
        We change the fixture accordingly
        """
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
