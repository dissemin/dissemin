from shibboleth.app_settings import GROUP_ATTRIBUTES
from website.backends import ShibbolethRemoteUserBackend
from shibboleth.middleware import ShibbolethRemoteUserMiddleware
from shibboleth.middleware import ShibbolethValidationError

from django.contrib import auth
from django.core.exceptions import ImproperlyConfigured


class ShibbolethRemoteUserMiddleware(ShibbolethRemoteUserMiddleware):
    """
    The subclassed middleware looks for the user by eppn, but we do not store eppn on user model, but in a linked class. So we have to get the user from there.
    """

    def process_request(self, request):
        """
        This function is almost identical to that of the super class, exxcept for retrieval of a user
        """
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the RemoteUserMiddleware class.")

        # Locate the remote user header.
        try:
            username = request.META[self.header]
        except KeyError:
            # If specified header doesn't exist then return (leaving
            # request.user set to AnonymousUser by the
            # AuthenticationMiddleware).
            # Or we logout the user if he was authenticated with this backend
            if request.user.is_authenticated:
                self._remove_invalid_user(request)
            return
        #If we got an empty value for request.META[self.header], treat it like
        #   self.header wasn't in self.META at all - it's still an anonymous user.
        if not username:
            return
        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        is_authenticated = request.user.is_authenticated
        # Here we do not look for the username of the authenticated user, but its shibbolethuser.shib_username
        if is_authenticated and hasattr(request.user, 'shibboleth_account'):
            if request.user.shibboleth_account.shib_username == self.clean_username(username, request):
                return

        # Make sure we have all required Shiboleth elements before proceeding.
        shib_meta, error = self.parse_attributes(request)
        # Add parsed attributes to the session.
        request.session['shib'] = shib_meta
        if error:
            raise ShibbolethValidationError("All required Shibboleth elements"
                                            " not found.  %s" % shib_meta)

        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        user = auth.authenticate(request, remote_user=username, shib_meta=shib_meta)
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            auth.login(request, user)

            # Upgrade user groups if configured in the settings.py
            # If activated, the user will be associated with those groups.
            if GROUP_ATTRIBUTES:
                self.update_user_groups(request, user)
            # call make profile.
            self.make_profile(user, shib_meta)
            # setup session.
            self.setup_session(request)

    def _remove_invalid_user(self, request):
        """
        Remove the current authenticated user in the request which is invalid
        but only if the user is authenticated via the ShibbolethRemoteUserBackend.
        """
        try:
            stored_backend = auth.load_backend(request.session.get(auth.BACKEND_SESSION_KEY, ''))
        except ImportError:
            # backend failed to load
            auth.logout(request)
        else:
            if isinstance(stored_backend, ShibbolethRemoteUserBackend):
                auth.logout(request)
