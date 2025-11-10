"""Audit Logging Middleware

Logs all API requests for security and compliance.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests"""

    async def dispatch(self, request: Request, call_next):
        # Record start time
        start_time = datetime.utcnow()

        # Extract request information
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else 'unknown'
        user_agent = request.headers.get('user-agent', 'unknown')

        # Get user if authenticated
        user_id = None
        username = None
        if hasattr(request.state, 'user'):
            user = request.state.user
            user_id = user.id if hasattr(user, 'id') else None
            username = user.username if hasattr(user, 'username') else None

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Log audit entry
        from ..database import SessionLocal
        from ..models.audit import AuditLog

        try:
            db = SessionLocal()

            audit_log = AuditLog(
                user_id=user_id,
                username=username,
                action=f"{method} {path}",
                resource_type=path.split('/')[2] if len(path.split('/')) > 2 else None,
                ip_address=client_host,
                user_agent=user_agent,
                request_method=method,
                request_path=path,
                status_code=response.status_code,
                metadata={
                    'duration_ms': duration_ms,
                    'response_size': len(response.body) if hasattr(response, 'body') else None
                }
            )

            db.add(audit_log)
            db.commit()

        except Exception as e:
            logger.error(f"Error logging audit entry: {e}")
        finally:
            db.close()

        # Add audit header to response
        response.headers['X-Request-ID'] = str(audit_log.id) if 'audit_log' in locals() else 'unknown'

        return response
