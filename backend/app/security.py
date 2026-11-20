import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

_bearer = HTTPBearer(auto_error=False)


async def require_operator(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    """
    Protects state-changing operations with a server-side bearer token.

    Local development remains convenient when no token is configured.
    Production fails closed if the secret has not been configured.
    """
    expected = settings.api_access_token

    if not expected:
        if settings.environment == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Operator access is not configured",
            )
        return

    supplied = credentials.credentials if credentials else ""
    if not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid operator access key is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
