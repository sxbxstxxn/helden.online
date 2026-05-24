import base64
import binascii
import secrets

from django.conf import settings
from django.http import HttpResponse


class SitePasswordMiddleware:
    """Protect the whole site with temporary HTTP Basic Auth when enabled."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.SITE_PASSWORD_ENABLED:
            return self.get_response(request)

        username, password = self._credentials_from_request(request)
        if self._credentials_are_valid(username, password):
            return self.get_response(request)

        response = HttpResponse('Authentifizierung erforderlich.', status=401)
        response['WWW-Authenticate'] = 'Basic realm="Helden Online"'
        return response

    def _credentials_from_request(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Basic '):
            return None, None

        try:
            decoded = base64.b64decode(auth_header.removeprefix('Basic ')).decode()
        except (binascii.Error, UnicodeDecodeError):
            return None, None

        username, separator, password = decoded.partition(':')
        if not separator:
            return None, None

        return username, password

    def _credentials_are_valid(self, username, password):
        expected_username = settings.SITE_PASSWORD_USERNAME
        expected_password = settings.SITE_PASSWORD

        if not expected_username or not expected_password:
            return False

        return (
            secrets.compare_digest(username or '', expected_username)
            and secrets.compare_digest(password or '', expected_password)
        )
