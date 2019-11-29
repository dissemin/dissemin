import pytest

from datetime import date

from backend.doi import CiteprocError
from backend.doi import CiteprocAuthorError
from backend.doi import CiteprocContainerTitleError
from backend.doi import CiteprocDateError
from backend.doi import CiteprocDOIError
from backend.doi import CiteprocPubtypeError
from backend.doi import CiteprocTitleError
from backend.doi import Citeproc
from backend.doi import CrossRef
from papers.baremodels import BareName
from papers.doi import doi_to_url


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


    def test_get_container(self, container_title, citeproc):
        """
        Must return container title
        """
        assert self.test_class._get_container(citeproc) == container_title

    def test_get_container_missing(self):
        """
        Must return exception
        """
        with pytest.raises(CiteprocContainerTitleError):
            self.test_class._get_container(dict())


    def test_get_doi(self, citeproc):
        """
        Must return the DOI
        """
        assert self.test_class._get_doi(citeproc) == citeproc['DOI']

    def test_get_doi_invalid(self):
        """
        Must raise exception
        """
        with pytest.raises(CiteprocDOIError):
            self.test_class._get_doi({'DOI' : 'spanish inquisition'})

    def test_get_doi_missing(self):
        """
        Must raise exception
        """
        with pytest.raises(CiteprocDOIError):
            self.test_class._get_doi(dict())


    @pytest.mark.parametrize('issn, expected', [('1234-5675', '1234-5675'), (['1234-5675', ], '1234-5675'), ([], '')])
    def test_get_issn(self, citeproc, issn, expected):
        """
        Must return the issn or ''
        """
        citeproc['ISSN'] = issn
        assert self.test_class._get_issn(citeproc) == expected

    def test_get_issn_missing(self, citeproc):
        """
        Must return ''
        """
        del citeproc['ISSN']
        assert self.test_class._get_issn(citeproc) == ''


    def test_get_oairecord_data(self, container_title, issn, citeproc):
        """
        We do some assertions on the results, but relatively lax, as we test the called functions, too
        """
        r = self.test_class._get_oairecord_data(citeproc)
        assert r['journal_title'] == container_title
        assert r['doi'] == citeproc['DOI']
        assert r['issn'] == issn
        assert r['issue'] == citeproc['issue']
        assert r['pages'] == citeproc['pages']
        assert r['publisher_name'] == citeproc['publisher_name']
        assert r['pubtype'] == citeproc['type']
        assert r['splash_url'] == doi_to_url(citeproc['DOI'])
        assert r['pdf_url'] == '' # Is not OA
        assert r['volume'] == citeproc['volume']


    def test_get_oairecord_data_missing(self, container_title, issn, citeproc):
        """
        Some fields must be empty, namely those with a direct get call
        """
        keys = ['issue', 'publisher_name', 'pages', 'volume']
        for k in keys:
            del citeproc[k]
        r = self.test_class._get_oairecord_data(citeproc)
        for k in keys:
            assert r[k] == ''



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


    @pytest.mark.parametrize('doi', [True, False])
    @pytest.mark.parametrize('license', [True, False])
    def test_get_pdf_url(self, monkeypatch, doi, license):
        """
        Must return true or false
        """
        monkeypatch.setattr(self.test_class, '_is_oa_by_doi', lambda x: doi)
        monkeypatch.setattr(self.test_class, '_is_oa_by_license', lambda x: license)
        url = 'https://repository.dissem.in/entry/3242/document.pdf'
        r = self.test_class._get_pdf_url(doi, license, url)
        if doi or license:
            assert r == url
        else:
            assert r == ''


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


    def test_get_pubtype(self):
        """
        Must return something from PAPER_TYPES
        """
        pubtype = 'book'
        assert self.test_class._get_pubtype({'type' : pubtype}) == pubtype

    def test_get_pubtype_strange(self):
        """
        Must return other
        """
        assert self.test_class._get_pubtype({'type' : 'spanish inquisition'}) == 'other'

    def test_get_pubtype_missing(self):
        """
        Must raise exception
        """
        with pytest.raises(CiteprocPubtypeError):
            self.test_class._get_pubtype(dict())

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


    @pytest.mark.parametrize('doi, expected', [('10.2195/spam', True), ('10.15122/spam', False)])
    def test_is_oa_by_doi(self, doi, expected):
        """
        Must be true or false
        """
        assert self.test_class._is_oa_by_doi(doi) == expected

    @pytest.mark.parametrize('licenses, expected', [([{'URL' : 'creativecommons.org/licenses/'}], True), ([{'URL' : 'https://dissem.in/not_free'}], False), ([{}], False), ([], False)])
    def test_is_oa_by_license(self, licenses, expected):
        """
        Must be true or false
        """
        assert self.test_class._is_oa_by_license(licenses) == expected


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
    def citeproc(self, container_title, title, citeproc):
        """
        In general, the CrossRef is identical to citeproc, but there are some differences.
        We change the fixture accordingly
        title is a list
        container-title is a list
        """
        citeproc['title'] = [title, ]
        citeproc['container-title'] = [container_title, ]

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
