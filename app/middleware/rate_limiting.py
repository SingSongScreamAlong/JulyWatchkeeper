"""Rate Limiting Middleware

Protects API endpoints from abuse using Redis-based rate limiting.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import os
from datetime import datetime

# Redis connection
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests"""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute

    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP or user_id)
        client_id = request.client.host if request.client else 'unknown'

        if hasattr(request.state, 'user'):
            user = request.state.user
            if hasattr(user, 'id'):
                client_id = f"user:{user.id}"

        # Create rate limit key
        current_minute = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        key = f"rate_limit:{client_id}:{current_minute}"

        try:
            # Increment counter
            current_requests = redis_client.incr(key)

            # Set expiry on first request
            if current_requests == 1:
                redis_client.expire(key, 60)

            # Check if exceeded
            if current_requests > self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Max {self.requests_per_minute} requests per minute."
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers['X-Rate-Limit-Limit'] = str(self.requests_per_minute)
            response.headers['X-Rate-Limit-Remaining'] = str(
                max(0, self.requests_per_minute - current_requests)
            )

            return response

        except redis.exceptions.RedisError as e:
            # If Redis fails, allow request but log error
            import logging
            logging.error(f"Redis error in rate limiting: {e}")
            return await call_next(request)
