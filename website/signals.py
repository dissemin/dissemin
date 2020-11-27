from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.signals import pre_social_login
from allauth.account.signals import user_logged_in

from django.shortcuts import render
from django.utils.translation import ugettext as _

from papers.models import Researcher
from papers.utils import validate_orcid
from website.models import ShibbolethUser
from website.utils import merge_users


def fetch_on_orcid_login(sender, sociallogin, **kwargs):
    """
    Here we prepare some things, i.e. create a Researcher and require that the name on the orcid profile is public
    """
    account = sociallogin.account

    # Only prefetch if the social login refers to a valid ORCID account
    orcid = validate_orcid(account.uid)
    if not orcid:
        raise ImmediateHttpResponse(
            render(
                kwargs['request'],
                'dissemin/error.html',
                {'message':_('Invalid ORCID identifier.')}
            )
        )

    profile = None # disabled account.extra_data because of API version mismatches
    user = None
    if '_user_cache' in account.__dict__:
        user = account.user
    r = Researcher.get_or_create_by_orcid(orcid, profile, user)

    if not r: # invalid ORCID profile (e.g. no name provided)
        raise ImmediateHttpResponse(
            render(
                kwargs['request'],
                'dissemin/error.html',
                {'message': _(
                    'Dissemin requires access to your ORCID name, '
                    'which is marked as private in your ORCID profile.'
                )}
            )
        )

def complete_researcher_profile_on_orcid_login(sender, user, **kwargs):
    """
    The researcher does exist, so we can connect the authenticated user to it if not yet done
    In case that the researcher already has a different user, we check wether it is a shibboleth authenticated user; if so, we merge and delete one of the users
    """
    orcid = user.socialaccount_set.first().uid
    r = Researcher.objects.get(orcid=orcid)

    # The researcher does not have a user yet, this is simple
    if r.user_id is None:
        r.user = user
        r.save(update_fields=['user'])
    # There's a user
    else:
        # Let's see if there's a shibboleth user
        try:
            shib_account = ShibbolethUser.objects.get(user=r.user)
        except ShibbolethUser.DoesNotExist:
            # This must be a different user, i.e. from ORCID or some custom user
            pass
        else:
            # Here we do have a shibboleth user attached to the researcher
            # We need to merge the user, change the concordance in ShibbolethUser and delete the no longer used user
            shib_user = shib_account.user
            merge_users(user, shib_user)
            r.user = user
            r.save(update_fields=['user'])
            shib_account.user = user
            shib_account.save()
            shib_user.delete()

    # Finally, let's make sure that the profile is up to date
    if r.empty_orcid_profile is None:
        r.init_from_orcid()
    else:
        r.fetch_everything_if_outdated()

# Register signals
pre_social_login.connect(fetch_on_orcid_login)
user_logged_in.connect(complete_researcher_profile_on_orcid_login)
