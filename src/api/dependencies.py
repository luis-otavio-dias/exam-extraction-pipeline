"""FastAPI dependencies for authentication and common concerns."""

import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from config import CONFIG

_api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str:
    """Validate the X-Api-Key header against the configured secret.

    Uses ``secrets.compare_digest`` to prevent timing-attack leaks.

    Raises:
        HTTPException 403: If the key is missing or invalid.

    Returns:
        The validated API key string.
    """
    expected = CONFIG.api.secret_key
    if not expected:
        msg = "API_SECRET_KEY is not configured on the server."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg,
        )

    if api_key is None or not secrets.compare_digest(api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key.",
        )

    return api_key
