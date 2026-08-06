from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(
    name=settings.API_KEY_NAME,
    auto_error=False,
)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Verify X-API-Key header for protected endpoints.
    """

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing.",
        )

    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return api_key