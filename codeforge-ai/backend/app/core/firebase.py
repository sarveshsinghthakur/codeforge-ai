"""Firebase ID token verification using Google's Secure Token certificates."""
import time

import httpx
from jose import JWTError, jwt

from app.core.config import settings

CERTS_URL = (
    "https://www.googleapis.com/robot/v1/metadata/x509/"
    "securetoken@system.gserviceaccount.com"
)
CERTS_TTL_SECONDS = 3600

_cache: dict = {"keys": None, "fetched_at": 0.0}


class InvalidFirebaseToken(ValueError):
    """Raised when a Firebase ID token fails verification."""


def _get_certificates(force_refresh: bool = False) -> dict:
    now = time.time()
    if (
        not force_refresh
        and _cache["keys"]
        and now - _cache["fetched_at"] < CERTS_TTL_SECONDS
    ):
        return _cache["keys"]
    try:
        resp = httpx.get(CERTS_URL, timeout=10.0)
        resp.raise_for_status()
        keys = resp.json()
    except httpx.HTTPError as exc:
        raise InvalidFirebaseToken("Unable to fetch signing certificates") from exc
    if not isinstance(keys, dict) or not keys:
        raise InvalidFirebaseToken("Empty signing certificate response")
    _cache["keys"] = keys
    _cache["fetched_at"] = now
    return keys


def verify_firebase_id_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return its claims.

    Validates signature (Google Secure Token certs), expiry, audience and
    issuer against the configured Firebase project.
    """
    if not id_token or not isinstance(id_token, str):
        raise InvalidFirebaseToken("Missing credential")

    try:
        header = jwt.get_unverified_header(id_token)
    except JWTError as exc:
        raise InvalidFirebaseToken("Malformed token") from exc

    kid = header.get("kid")
    if not kid:
        raise InvalidFirebaseToken("Token missing key id")

    keys = _get_certificates()
    if kid not in keys:
        keys = _get_certificates(force_refresh=True)
    if kid not in keys:
        raise InvalidFirebaseToken("Unknown signing key")

    project_id = settings.firebase_project_id
    try:
        claims = jwt.decode(
            id_token,
            keys[kid],
            algorithms=["RS256"],
            audience=project_id,
            issuer=f"https://securetoken.google.com/{project_id}",
        )
    except JWTError as exc:
        raise InvalidFirebaseToken(str(exc)) from exc

    if not claims.get("sub"):
        raise InvalidFirebaseToken("Token missing subject")
    return claims
