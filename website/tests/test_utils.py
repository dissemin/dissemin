import pytest
import time

from django.contrib.auth.models import User

from deposit.hal.models import HALDepositPreferences
from deposit.models import DepositRecord
from deposit.models import UserPreferences
from deposit.osf.models import OSFDepositPreferences
from website.utils import merge_users


@pytest.mark.usefixtures('db')
class TestUserMerge:
    """
    Groups tests about merging of User objects
    """

    @pytest.fixture(autouse=True)
    def preparation(self, db):
        """
        Sets up two users that can be merged
        """
        self.user_1 = User.objects.create_user(
            username='user_1',
        )
        # Some time between creation, to have measurable different joined dates
        time.sleep(1)
        self.user_2 = User.objects.create_user(
            username='user_2',
            email='user_2@dissem.in',
            first_name='Iulius',
            last_name='Caesar',
        )

    def test_monitor_relations(self):
        """
        Monitors the relations of the User model. Of particual interest are reverse relations.
        If this test fails, then a new field or relation has been added. Make sure to adjust the merging
        """
        field_names = {
            'date_joined',
            'depositrecord',
            'email',
            'emailaddress',
            'first_name',
            'groups',
            'haldepositpreferences',
            'id',
            'inbox',
            'is_active',
            'is_staff',
            'is_superuser',
            'last_login',
            'last_name',
            'logentry',
            'notificationarchive',
            'osfdepositpreferences',
            'paper',
            'password',
            'researcher',
            'shibbolethuser',
            'socialaccount',
            'uploadedpdf',
            'user_permissions',
            'username',
            'userpreferences'
            }
        assert { field.name for field in User._meta.get_fields() } == field_names

    def test_merge(self, dummy_repository, book_god_of_the_labyrinth, uploaded_pdf):
        dr = DepositRecord.objects.create(
            paper=book_god_of_the_labyrinth,
            user=self.user_2,
            repository=dummy_repository,
            status='pending',
            file=uploaded_pdf,
        )
        # Let's merge
        merge_users(self.user_1, self.user_2)

        # Then we do our checks
        # Fields where we can merge directly
        for field in ['email', 'first_name', 'last_name',]:
            assert getattr(self.user_1, field) == getattr(self.user_2, field)
        # Date joined, should be the older one
        assert self.user_1.date_joined <= self.user_2.date_joined

        dr.refresh_from_db()

        # We do not test all fields, as they are the same, but at least one
        assert dr.user == self.user_1


    def test_repository_preferences(self, repository):
        obo = 'spam'
        hal_rep = repository.dummy_repository()
        osf_rep = repository.dummy_repository()
        assert hal_rep.pk != osf_rep.pk
        HALDepositPreferences.objects.create(user=self.user_2, repository=hal_rep)
        OSFDepositPreferences.objects.create(user=self.user_1, repository=osf_rep)
        OSFDepositPreferences.objects.create(user=self.user_2, repository=osf_rep, on_behalf_of=obo)
        self.user_1.refresh_from_db()
        self.user_2.refresh_from_db()
        merge_users(self.user_1, self.user_2)
        self.user_1.refresh_from_db()
        assert len(self.user_1.haldepositpreferences_set.all()) == 1
        assert self.user_1.osfdepositpreferences_set.get().on_behalf_of == obo


    def test_merge_one_to_one_relation_change_obj(self):
        """
        Does not test all fields, but the process
        """
        email = 'user@dissem.in'
        UserPreferences.objects.create(user=self.user_2, email=email)
        merge_users(self.user_1, self.user_2)
        self.user_1.refresh_from_db()
        assert self.user_1.userpreferences.email == email
        self.user_2.refresh_from_db()
        assert hasattr(self.user_2, 'userpreferences') == False

    def test_merge_one_to_one_relation_change_field_values(self, dummy_repository):
        """
        Does not test all fields, but the process
        """
        UserPreferences.objects.create(user=self.user_1, last_repository=dummy_repository)
        email = 'user@dissem.in'
        UserPreferences.objects.create(user=self.user_2, email=email)
        merge_users(self.user_1, self.user_2)
        self.user_1.refresh_from_db()
        assert self.user_1.userpreferences.email == email
        assert self.user_1.userpreferences.last_repository == dummy_repository
