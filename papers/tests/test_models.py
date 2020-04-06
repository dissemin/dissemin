# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#



import datetime
import doctest
import os
import pytest

from datetime import date
from mock import patch

import django.test


from django.contrib.auth.models import User

import papers.doi

from oaipmh.client import Client
from papers.baremodels import BareName
from papers.models import Name
from papers.models import OaiRecord
from papers.models import OaiSource
from papers.models import Paper
from papers.models import Researcher
from papers.models import Institution
from publishers.tests.test_romeo import RomeoAPIStub

class TestPaper():
    """
    Class that groups tests for Paper class
    """

    def test_create_by_doi_metadata_error(self, monkeypatch):
        """
        If CiteprocError is raised inside called function, expect a silent None
        """
        from backend.citeproc import DOIResolver
        from backend.citeproc import CiteprocError
        def raise_citeproc(*args, **kwargs):
            raise CiteprocError
        monkeypatch.setattr(DOIResolver, 'save_doi', raise_citeproc)
        p = Paper.create_by_doi('not_important')
        assert p is None

    @pytest.mark.usefixtures('db', 'mock_doi')
    def test_create_by_doi_invalid_doi(self):
        p = Paper.create_by_doi('10.1021/eiaeuiebop134223cen-v043n050.p033')
        assert p is None

    def test_create_by_doi_requests_error(self, monkeypatch):
        """
        If RequestException is raised inside called function, expect a silent None
        """
        from backend.citeproc import DOIResolver
        from requests.exceptions import RequestException
        def raise_citeproc(*args, **kwargs):
            raise RequestException
        monkeypatch.setattr(DOIResolver, 'save_doi', raise_citeproc)
        p = Paper.create_by_doi('not_important')
        assert p is None


    @pytest.mark.parametrize('on_list', [True, False])
    def test_on_todolist(self, book_god_of_the_labyrinth, user_isaac_newton, on_list):
        if on_list:
            book_god_of_the_labyrinth.todolist.add(user_isaac_newton)
        assert book_god_of_the_labyrinth.on_todolist(user_isaac_newton) == on_list


@pytest.mark.usefixtures('db', 'mock_doi')
class TestPaperDOIUsage():
    """
    Class that groups tests for Paper class that do calls to doi.org
    """

    def test_create_by_doi(self):
        # we recapitalize the DOI to make sure it is treated in a
        # case-insensitive way internally
        p = Paper.create_by_doi('10.1109/sYnAsc.2010.88')
        assert p.title == 'Monitoring and Support of Unreliable Services'
        assert p.publications[0].doi == '10.1109/synasc.2010.88'
        print(p.publications[0].last_update)


    def test_create_by_doi_no_authors(self):
        p = Paper.create_by_doi('10.1021/cen-v043n050.p033')
        assert p is None

    def test_create_by_doi_publication_pdf_url(self):
        # This journal is open access
        romeo = RomeoAPIStub()
        journal = romeo.fetch_journal({'issn':'0250-6335'})
        # Therefore any paper in it is available from the publisher
        p = Paper.create_by_doi('10.1007/BF02702259')
        assert p.publications[0].journal == journal
        # so the pdf_url of the publication should be set
        p.publications[0].pdf_url.lower() == 'https://doi.org/10.1007/BF02702259'.lower()


    def test_merge(self):
        # Get a paper with metadata
        p = Paper.create_by_doi('10.1111/j.1744-6570.1953.tb01038.x')
        p = Paper.from_bare(p)
        # Create a copy with slight variations
        names = [BareName.create_bare(f, l) for (f, l) in
                 [('M. H.', 'Jones'), ('R. H.', 'Haase'), ('S. F.', 'Hulbert')]]
        p2 = Paper.get_or_create(
                'A Survey of the Literature on Technical Positions', names,
                date(year=2011, month=0o1, day=0o1))
        # The two are not merged because of the difference in the title
        assert p != p2
        # Fix the title of the second one
        p2.title = 'A Survey of the Literature on Job Analysis of Technical Positions'
        p2.save()
        # Check that the new fingerprint is equal to that of the first paper
        assert p2.new_fingerprint() == p.fingerprint
        # and that the new fingerprint and the current differ
        assert p2.new_fingerprint() != p2.fingerprint
        # and that the first paper matches its own shit
        assert Paper.objects.filter(fingerprint=p.fingerprint).first() == p
        # The two papers should hence be merged together
        new_paper = p2.recompute_fingerprint_and_merge_if_needed()
        assert new_paper.pk == p.pk

    def test_merge_attributions_preserved(self):
        """
        If papers merged, researchers must preserve
        """
        p1 = Paper.create_by_doi('10.4049/jimmunol.167.12.6786')
        r1 = Researcher.create_by_name('Stephan', 'Hauschildt')
        p1.set_researcher(4, r1.id)
        p2 = Paper.create_by_doi('10.1016/j.chemgeo.2015.03.025')
        r2 = Researcher.create_by_name('Priscille', 'Lesne')
        p2.set_researcher(0, r2.id)

        # merge them ! even if they actually don't have anything
        # to do together
        p1.merge(p2)

        p1.check_authors()

        assert p1.researchers == [r2, r1]


    def test_owned_by(self):
        """
        Checks on paper owning
        """
        p = Paper.create_by_doi('10.4049/jimmunol.167.12.6786')
        r = Researcher.create_by_name('Stephan', 'Hauschildt')
        r.user, _ = User.objects.get_or_create(username='stephan')
        r.save()
        p.set_researcher(4, r.pk)
        # The user is associated to the author in the model,
        # so it is considered an owner.
        assert p.is_owned_by(r.user)
        other_user, _ = User.objects.get_or_create(
            username='AndreaThiele',
            first_name='Andrea',
            last_name='Thiele')
        # This other user is not associated to any researcher,
        # so it isn't associated to the paper.
        assert not p.is_owned_by(other_user)
        # But if we ask for a flexible check, as her name matches
        # one of the author names of the paper, she is recognized.
        assert p.is_owned_by(other_user, flexible=True)


    def test_set_researcher(self):
        """
        Test setting (adding and removing) the researcher
        """
        p = Paper.create_by_doi('10.4049/jimmunol.167.12.6786')
        r = Researcher.create_by_name('Stephan', 'Hauschildt')
        # Add the researcher
        p.set_researcher(4, r.pk)
        assert set(p.researchers) == {r}
        # Remove the researcher
        p.set_researcher(4, None)
        assert set(p.researchers) == set()


class InstitutionTest(django.test.TestCase):
    def test_valid(self):
        institution = {
            'country': 'FR',
            'name': '  Université Paris 8 ',
            'identifier': 'ringgold-23478',
        }
        i = Institution.create(institution)
        self.assertEqual(i.country.code, institution['country'])
        self.assertEqual(i.name, institution['name'].strip())
        self.assertTrue(institution['identifier'] in i.identifiers)

    def test_too_long(self):
        institution = {
            'country': 'RU',
            'identifier': None,
            'name': """
            Не знаете как вылечить туберкулез - мы вам
            подскажем, достаточно заказать азиатскую медведку и начать ее принимать.
            Способ применения достаточно прост, а эффект потрясающий. Не ждите, ведь
            завтра может быть уже поздно. Звоните по тел +796О8887578 или заходите на
            сайт http://kypit-medvedki.ru/
            """}
        # This institution is too long for our model!
        self.assertEqual(
            Institution.create(institution),
            None)

    def test_invalid_country_code(self):
        institution = {
            'country': 'XX',
            'identifier': None,
            'name': 'University of planet earth'}

        self.assertEqual(
            Institution.create(institution),
            None)


@pytest.mark.usefixtures('db')
class TestResearcher:

    def test_creation(self):
        r = Researcher.create_by_name('George', 'Banks')
        r2 = Researcher.create_by_name(' George', ' Banks')
        assert r != r2

        r3 = Researcher.get_or_create_by_orcid('0000-0003-2306-6531',
            instance='sandbox.orcid.org')
        assert r != r3

    def test_empty_name(self):
        r = Researcher.create_by_name('', '')
        assert r is None
        # this ORCID has no public name in the sandbox:
        r = Researcher.get_or_create_by_orcid('0000-0002-6091-2701',
            instance='sandbox.orcid.org')
        assert r is None

    def test_institution(self):
        r = Researcher.get_or_create_by_orcid('0000-0002-0022-2290',
            instance='sandbox.orcid.org')
        assert r.institution.name == 'Ecole Normale Superieure'

    def test_institution_match(self):
        # first, load a profile from someone with
        # a disambiguated institution (from the sandbox)
        # http://sandbox.orcid.org/0000-0001-7174-97
        r = Researcher.get_or_create_by_orcid('0000-0001-7174-9738',
            instance='sandbox.orcid.org')
        # then, load someone else, with the same institution, but not
        # disambiguated, and without accents
        # http://sandbox.orcid.org//0000-0001-6068-024
        r2 = Researcher.get_or_create_by_orcid('0000-0001-6068-0245',
            instance='sandbox.orcid.org')
        assert r.institution == r2.institution

    def test_refresh(self):
        r = Researcher.get_or_create_by_orcid('0000-0002-0022-2290',
                    instance='sandbox.orcid.org')
        assert r.institution.name == 'Ecole Normale Superieure'
        r.institution = None
        r.name = Name.lookup_name(('John','Doe'))
        r.save()
        r = Researcher.get_or_create_by_orcid('0000-0002-0022-2290',
                instance='sandbox.orcid.org',
                update=True)
        assert r.institution.name == 'Ecole Normale Superieure'


    def test_name_conflict(self):
        # Both are called "John Doe"
        r1 = Researcher.get_or_create_by_orcid('0000-0002-3037-8851',
            instance='sandbox.orcid.org')
        r2 = Researcher.get_or_create_by_orcid('0000-0003-2295-9629',
            instance='sandbox.orcid.org')
        assert r1 != r2

    def test_merge_monitor_fields(self):
        """
        We monitor fields. If we get a new field, we have to adjust the corresponding merge function.
        So if we add or remove a field to Researcher, this test will fail!
        """
        field_names = {'id', 'name', 'user', 'department', 'institution', 'email', 'homepage', 'role', 'orcid', 'empty_orcid_profile', 'last_harvest', 'harvester', 'current_task', 'stats', 'visible'}
        assert set(field.name for field in Researcher._meta.get_fields()) == field_names

    @pytest.mark.usefixtures('mock_doi')
    @pytest.mark.parametrize('delete_user', [True, False])
    def test_merge(self, delete_user, django_user_model):
        u = django_user_model.objects.create(
            username='becks',
            first_name='Stefan',
            last_name='Beck'
        )
        r = Researcher.create_by_name('Stefan', 'Beck', email='stefan.beck@ulb.tu-darmstadt.de', homepage='https://becks.dissem.in', user=u)
        u2 = django_user_model.objects.create(
            username='becks2',
            first_name='Stefan',
            last_name='Beck'
        )
        r2 = Researcher.create_by_name('Stefan', 'Beck', orcid='0000-0001-8187-9704', homepage='https://sbeck.dissem.in', user=u2)
        p = Paper.create_by_doi('10.17192/z2016.0217')
        p.set_researcher(0, r2.pk)
        p.save()
        r.merge(r2, delete_user=delete_user)
        p.refresh_from_db()
        r.refresh_from_db()
        assert r.name == r2.name
        assert r.email == 'stefan.beck@ulb.tu-darmstadt.de'
        assert r.homepage == 'https://becks.dissem.in'
        assert r.orcid == r2.orcid
        assert p.authors_list[0]['researcher_id'] == r.pk
        with pytest.raises(Researcher.DoesNotExist):
            r2.refresh_from_db()
        if delete_user:
            with pytest.raises(django_user_model.DoesNotExist):
                u2.refresh_from_db()
        else:
            u2.refresh_from_db()

    def test_merge_value_error(self):
        r = Researcher.create_by_name('Stefan', 'Beck', email='stefan.beck@ulb.tu-darmstadt.de', homepage='https://becks.dissem.in')
        r2 = Researcher.create_by_name('Stefan', 'Beck', homepage='https://sbeck.dissem.in')
        with pytest.raises(ValueError):
            r.pk = None
            r.merge(r2)
        r.save()
        with pytest.raises(ValueError):
            r2.pk = None
            r.merge(r2)
        r.save()
        with pytest.raises(ValueError):
            r2.pk = r.pk
            r.merge(r2)


class NameTest(django.test.TestCase):
    def test_max_length(self):
        # The long string is shorter than the max name length,
        # but becomes longer after escaping of the & sign
        self.assertEqual(
            Name.lookup_name(("""
an ISO 9001 Certified Instrumentation
Company in India manufactures hi-tech Calibration Instruments & Systems
for Pressure, Temperature & Electrical parameters. Many of our
Temperature & Pressure Calibrator Models are Certified by DNV. Nagman
also""", "Nagman")),
            None)

class OaiRecordTest(django.test.TestCase):

    @classmethod
    def setUpClass(self):
        super(OaiRecordTest, self).setUpClass()
        self.source = OaiSource.objects.get_or_create(identifier='arxiv',
                                                      defaults={'name': 'arXiv', 'oa': False, 'priority': 1, 'default_pubtype': 'preprint'})

    def test_find_duplicate_records_invalid_url(self):
        paper = Paper.get_or_create('this is a title', [Name.lookup_name(('Jean', 'Saisrien'))],
                                    datetime.date(year=2015, month=0o5, day=0o4))
        # This used to throw an exception
        OaiRecord.find_duplicate_records(
            paper, 'ftp://dissem.in/paper.pdf', None)


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(papers.doi))
    return tests


class PaperTest(django.test.TestCase):

    @classmethod
    def setUpClass(self):
        super(PaperTest, self).setUpClass()
        self.testdir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(self.testdir, 'data/citeseerx_record_without_date.xml'), 'r') as f:
            self.citeseerx_record_without_date = f.read()
        with open(os.path.join(self.testdir, 'data/pmc_record.xml'), 'r') as f:
            self.pmc_record = f.read()
        with open(os.path.join(self.testdir, 'data/hal_record.xml'), 'r') as f:
            self.hal_record = f.read()

    @patch.object(Client, 'makeRequest')
    def test_create_by_identifier_no_pubdate(self, mock_makeRequest):
        citeseerx = OaiSource(identifier='citeseerx', name='CiteSeerX', endpoint='http://example.com/')
        citeseerx.save()
        mock_makeRequest.return_value = self.citeseerx_record_without_date

        # Paper has no date
        p = Paper.create_by_oai_id('oai:CiteSeerX.psu:10.1.1.487.869', source=citeseerx)
        self.assertEqual(p, None)

    @patch.object(Client, 'makeRequest')
    def test_create_by_identifier_valid_paper(self, mock_makeRequest):
        pmc = OaiSource.objects.get(identifier='pmc')
        mock_makeRequest.return_value = self.pmc_record

        p = Paper.create_by_oai_id('oai:pubmedcentral.nih.gov:4131942', source=pmc)
        self.assertEqual(p.pdf_url, 'http://www.ncbi.nlm.nih.gov/pmc/articles/PMC4131942/')

    @patch.object(Client, 'makeRequest')
    def test_create_by_hal_id(self, mock_makeRequest):
        mock_makeRequest.return_value = self.hal_record

        p = Paper.create_by_hal_id('hal-00830421')
        self.assertEqual(p.oairecords[0].splash_url, 'https://hal.archives-ouvertes.fr/hal-00830421')

