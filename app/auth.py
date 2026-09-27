from fastapi import Header, HTTPException, Query

from .config import settings


def _valid_bearer(authorization: str | None) -> bool:
    return bool(settings.app_token) and authorization == f"Bearer {settings.app_token}"


def require_token(authorization: str | None = Header(default=None)):
    if not settings.app_token or _valid_bearer(authorization):
        return
    raise HTTPException(status_code=401, detail="Invalid token")


def require_media_token(
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
):
    # HTML <audio> elements cannot attach an Authorization header, so media
    # endpoints also accept the token as a query parameter. Prefer Bearer auth
    # for API calls and native clients.
    if not settings.app_token or _valid_bearer(authorization) or token == settings.app_token:
        return
    raise HTTPException(status_code=401, detail="Invalid token")
