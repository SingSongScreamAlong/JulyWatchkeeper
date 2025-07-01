from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from src.core.config import settings

api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    """
    Validate API key from header.
    
    Args:
        api_key_header: API key from request header
        
    Returns:
        Validated API key
        
    Raises:
        HTTPException: If API key is invalid
    """
    if api_key_header == settings.API_KEY:
        return api_key_header
    
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail="Could not validate API key",
    )


def verify_secret_key(secret_key: str) -> bool:
    """
    Verify if the provided secret key matches the application secret key.
    
    Args:
        secret_key: Secret key to verify
        
    Returns:
        True if secret key is valid, False otherwise
    """
    return secret_key == settings.SECRET_KEY


def generate_secure_token() -> str:
    """
    Generate a secure random token for temporary authentication.
    
    Returns:
        Secure random token
    """
    import secrets
    return secrets.token_urlsafe(32)
