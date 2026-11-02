import hashlib
import hmac
import secrets

from hr_aiaas.config import get_settings

SESSION_COOKIE = "hr_aiaas_session"
CSRF_COOKIE = "hr_aiaas_csrf"
CSRF_HEADER = "X-CSRF-Token"


def new_session_token() -> str:
    return secrets.token_urlsafe(48)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def csrf_token_for(session_token: str) -> str:
    secret = get_settings().session_secret.get_secret_value().encode("utf-8")
    return hmac.new(secret, session_token.encode("utf-8"), hashlib.sha256).hexdigest()


def csrf_is_valid(session_token: str, cookie_token: str | None, header_token: str | None) -> bool:
    if not cookie_token or not header_token:
        return False
    expected = csrf_token_for(session_token)
    return hmac.compare_digest(cookie_token, expected) and hmac.compare_digest(header_token, expected)
