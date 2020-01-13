import responses

from requests.exceptions import RequestException
from requests.exceptions import HTTPError

from django.conf import settings

from backend.zotero import fetch_zotero_by_DOI

valid_response = [{'attachments': [], 'pages': '1028-1033', 'issue': '11', 'volume': '55', 'tags': [], 'creators': [{'firstName': 'A. M.', 'lastName': 'Beck', 'creatorType': 'author'}, {'firstName': 'L.', 'lastName': 'Ovesen', 'creatorType': 'author'}, {'firstName': 'M.', 'lastName': 'Schroll', 'creatorType': 'author'}], 'accessDate': '2020-01-10T15:41:38Z', 'rights': '2001 Macmillan Publishers Limited', 'DOI': '10.1038/sj.ejcn.1601266', 'ISSN': '1476-5640', 'publicationTitle': 'European Journal of Clinical Nutrition', 'url': 'https://www.nature.com/articles/1601266', 'abstractNote': "Objective: To assess the prevalence of old people at risk of undernutrition according to the Mini Nutritional Assessment (MNA), characterise the at risk group with regard to nutritional state, energy intake, and physical and mental functioning, and to assess the consequences of the MNA score over a 6 month period. Design: A cross-sectional prospective study. Setting: The clinic of a general practitioner. Subjects: Ninety-four patients 65+-y-old with no acute illness contacted at the clinic. Sixty-one subjects (65%) agreed to participate at baseline and 34 (56%) showed up at the follow-up 6 months later. Results: At baseline, 23 (38%) participants were assessed as being at risk of undernutrition (17–23.5\u2005MNA points). The remaining were classified as well-nourished (>23.5 MNA points). The 23 participants at risk had a higher prevalence of body mass index (BMI) <20\u2005kg/m2 (44 vs 11%, P<0.001) and insufficient energy intake (36 vs 9%, P<0.05), compared with the well-nourished group. Also, they had a higher need of meals-on-wheels (39 vs 8%, P<0.01) and home-care for shopping (48 vs 18%, P<0.05) at baseline. At the 6 months' follow-up, there was a tendency to a higher non-participation rate among the participants assessed at risk of undernutrition at baseline (44 vs 18%, 0.05<P<0.1), compared with the well-nourished group. There was a tendency to a higher prevalence of hospitalisation (38 vs 19%, 0.05<P<0.1) in the at risk group. Conclusion: MNA seems to be a useful tool to identify old people who need help from the public sector. However, many in the group at risk of undernutrition already have low BMI values. This might have influenced the findings. European Journal of Clinical Nutrition (2001) 55, 1028–1033", 'version': 0, 'itemType': 'journalArticle', 'key': 'VHGECGE8', 'title': "A six months' prospective follow-up of 65+-y-old patients from general practice classified according to nutritional risk by the Mini Nutritional Assessment", 'libraryCatalog': 'www.nature.com', 'language': 'en', 'date': '2001-11'}]


class TestFetchZoteroByDOI():
    """
    Test about function backend.zotero.fetch_zotero_by_DOI
    """

    @responses.activate
    def test_success(self):
        """
        Everything behaves fine, i.e. no HTTP Error and valid JSON
        """
        doi = '10.1038/sj/ejcn/1601266'
        responses.add(
            responses.GET,
            'https://{}/zotero/{}'.format(settings.DOI_PROXY_DOMAIN, doi),
            json=valid_response
        )
        r = fetch_zotero_by_DOI(doi)
        assert r == valid_response

    @responses.activate
    def test_connection_error(self, caplog):
        r = fetch_zotero_by_DOI('spam')
        assert r is None
        log_entry = caplog.records[0]
        assert log_entry.name == 'dissemin.backend.zotero'
        assert log_entry.levelname == 'ERROR'
        assert isinstance(log_entry.msg, RequestException)

    @responses.activate
    def test_http_status_error(self, caplog):
        """
        If HTTP status, expect NONE and logging entry
        """
        doi = '10.100/spam'
        responses.add(
            responses.GET,
            'https://{}/zotero/{}'.format(settings.DOI_PROXY_DOMAIN, doi),
            status=500
            )
        r = fetch_zotero_by_DOI(doi)
        assert r is None
        log_entry = caplog.records[0]
        assert log_entry.name == 'dissemin.backend.zotero'
        assert log_entry.levelname == 'ERROR'
        assert isinstance(log_entry.msg, HTTPError)

    @responses.activate
    def test_invalid_json(self, caplog):
        doi = '10.1038/invalid_json'
        responses.add(
            responses.GET,
            'https://{}/zotero/{}'.format(settings.DOI_PROXY_DOMAIN, doi),
            body='This is no JSON',
        )
        r = fetch_zotero_by_DOI(doi)
        assert r is None
        log_entry = caplog.records[0]
        assert log_entry.name == 'dissemin.backend.zotero'
        assert log_entry.levelname == 'ERROR'
        assert isinstance(log_entry.msg, ValueError)
