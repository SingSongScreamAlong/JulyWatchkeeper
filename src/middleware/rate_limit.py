"""
Rate Limiting Middleware for WATCHKEEPER

This module implements rate limiting using SlowAPI.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
import os


def get_api_key(request: Request) -> str:
    """
    Get API key from request for rate limiting.

    Uses API key if available, otherwise falls back to IP address.
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key}"
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_api_key,
    default_limits=[os.getenv("RATE_LIMIT_PER_MINUTE", "60/minute")],
    storage_uri=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)
