"""Header-based authentication used by the whole API.

Clients identify themselves with an ``X-User-Id: <user id>`` header. There are
no passwords in this practice app.
"""
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions


class HeaderUserAuthentication(authentication.BaseAuthentication):
    header = "X-User-Id"

    def authenticate(self, request):
        raw_id = request.headers.get(self.header)
        if not raw_id:
            return None  # not authenticated; permission classes decide what happens

        User = get_user_model()
        try:
            user = User.objects.get(pk=int(raw_id))
        except (ValueError, User.DoesNotExist):
            raise exceptions.AuthenticationFailed("Invalid X-User-Id header.")
        return (user, None)

    def authenticate_header(self, request):
        # Returning a value makes DRF answer 401 (not 403) when auth is missing.
        return self.header
