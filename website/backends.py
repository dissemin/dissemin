import logging

from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import User

from papers.models import Researcher
from papers.utils import validate_orcid
from website.models import ShibbolethAccount
from website.utils import merge_users

logger = logging.getLogger('dissemin.' + __name__)

class ShibbolethRemoteUserBackend(RemoteUserBackend):
    """
    We want to overwrite the user creation process to integrate ORCID.
    To this end we create a concordance between eduPersonPrincipalName and Django User objects and use this to get or create a User.
    This class is heavily inspired by shibboleth.backens.ShibbolethRemoteUserBackend
    """

    def authenticate(self, request, remote_user, shib_meta):
        """
        The remote_user is considered as trusted.
        Sets up a user based on shibboleth data.
        We file in website.models.ShibbolethAccount for it. If it does not exist, we create a user.
        If we have an orcid passed in the shib_meta, we try to find a researcher, otherwise we create a researcher.
        """
        # If no remote_user is given, we abort
        if not remote_user:
            logger.info('remote_user invalid')
            return

        logger.debug('Received remote_user: {}'.format(remote_user))

        # This is the real process of authentication
        shib_account = None
        try:
            shib_account = ShibbolethAccount.objects.get(shib_username=shib_meta.get('username'))
        except ShibbolethAccount.DoesNotExist:
            logger.debug("username {} not found".format(shib_meta.get('username')))

        orcid = validate_orcid(shib_meta.get('orcid'))

        if shib_account:
            logger.debug("Found ShibbolethAccount: {}".format(shib_account))
            # If we have a ShibbolethAccount object, we have a Researcher object
            researcher = Researcher.objects.get(user=shib_account.user)
            # If we have a ORCID, we can do some stuff
            if orcid:
                if researcher.orcid:
                    # If both objects have ORCIDs, we can assume that they are identical
                    return shib_account.user
                # Researcher object has no ORCID. We try to find a Researcher with that ORCID and merge, otherwise we can just set the ORCID to the current researcher
                try:
                    alt_researcher = Researcher.objects.get(orcid=orcid)
                except Researcher.DoesNotExist:
                    logger.debug("Found no researcher with orcid {}, save that on related researcher".format(orcid))
                    researcher.orcid = orcid
                    researcher.save()
                else:
                    # We have an alternative researcher. If there is user, merge them, otherwise proceed directly to merging researchers
                    if alt_researcher.user:
                        merge_users(shib_account.user, alt_researcher.user)
                    researcher.merge(alt_researcher, delete_user=True)
                return shib_account.user
            else:
                return shib_account.user

        # We have no ShibbolethAccount object
        # If we have an ORCID, we can try to find a Researcher
        if orcid:
            try:
                researcher = Researcher.objects.get(orcid=orcid)
            except Researcher.DoesNotExist:
                pass
            else:
                # We have found a Researcher object
                if researcher.user:
                    # The found researcher has a user object. We use it
                    ShibbolethAccount.objects.create(user=researcher.user, shib_username=shib_meta.get('username'))
                    return researcher.user
                else:
                    # The found researcher has no user object. We create a user and connect it
                    user = User.objects.create_user(
                        remote_user,
                        first_name=shib_meta.get('first_name'),
                        last_name=shib_meta.get('last_name'),
                    )
                    ShibbolethAccount.objects.create(user=user, shib_username=shib_meta.get('username'))
                    researcher.user = user
                    researcher.save()
                    return user

        # We have no ORCID, so we create a ShibbolethAccount and Researcher
        return self.create_new_user_and_researcher(remote_user, orcid, shib_meta)

    def create_new_user_and_researcher(self, remote_user, orcid, shib_meta):
        """
        Creates a new user and researcher and returns the user
        """
        user = User.objects.create_user(
            remote_user,
            first_name=shib_meta.get('first_name'),
            last_name=shib_meta.get('last_name'),
        )
        ShibbolethAccount.objects.create(user=user, shib_username=shib_meta.get('username'))
        Researcher.create_by_name(
            shib_meta.get('first_name'),
            shib_meta.get('last_name'),
            orcid=orcid,
            user=user,
        )
        return user
