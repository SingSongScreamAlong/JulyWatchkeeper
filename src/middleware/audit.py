"""
Audit Logging Middleware for WATCHKEEPER

This module implements comprehensive audit logging for all API operations.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import datetime
import json
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests for audit purposes."""

    def __init__(self, app: ASGIApp, enabled: bool = True):
        """
        Initialize audit middleware.

        Args:
            app: ASGI application
            enabled: Whether audit logging is enabled
        """
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log audit information.

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            Response from the route handler
        """
        if not self.enabled:
            return await call_next(request)

        # Capture request start time
        start_time = datetime.utcnow()

        # Extract user information from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)

        # Get client IP
        client_ip = request.client.host if request.client else None

        # Get user agent
        user_agent = request.headers.get("user-agent")

        # Process request
        response = await call_next(request)

        # Only log certain operations
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            try:
                from src.core.database import AsyncSessionLocal
                from src.models.audit_log import AuditLog, AuditAction

                # Determine action type
                action = None
                if request.method == "POST":
                    action = AuditAction.CREATE
                elif request.method == "PUT" or request.method == "PATCH":
                    action = AuditAction.UPDATE
                elif request.method == "DELETE":
                    action = AuditAction.DELETE

                # Extract resource type and ID from path
                path_parts = request.url.path.strip("/").split("/")
                resource_type = path_parts[-2] if len(path_parts) >= 2 else path_parts[-1] if path_parts else "unknown"
                resource_id = None

                # Try to extract ID from path
                if len(path_parts) >= 1:
                    try:
                        resource_id = int(path_parts[-1])
                    except ValueError:
                        resource_id = None

                # Create audit log entry
                async with AsyncSessionLocal() as session:
                    audit_log = AuditLog(
                        user_id=user_id,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        status="success" if response.status_code < 400 else "failure"
                    )

                    session.add(audit_log)
                    await session.commit()

                    logger.debug(f"Audit log created: {action} on {resource_type} by user {user_id}")

            except Exception as e:
                logger.error(f"Error creating audit log: {e}")

        return response


async def log_audit_event(
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: int = None,
    changes: dict = None,
    ip_address: str = None,
    status: str = "success",
    error_message: str = None
):
    """
    Manually log an audit event.

    Args:
        user_id: ID of the user performing the action
        action: Type of action (create, read, update, delete, etc.)
        resource_type: Type of resource affected
        resource_id: ID of the resource (optional)
        changes: Dict of changes made (optional)
        ip_address: IP address of the user (optional)
        status: Status of the action (success/failure)
        error_message: Error message if action failed (optional)
    """
    try:
        from src.core.database import AsyncSessionLocal
        from src.models.audit_log import AuditLog, AuditAction

        async with AsyncSessionLocal() as session:
            audit_log = AuditLog(
                user_id=user_id,
                action=AuditAction(action) if isinstance(action, str) else action,
                resource_type=resource_type,
                resource_id=resource_id,
                changes=changes,
                ip_address=ip_address,
                status=status,
                error_message=error_message
            )

            session.add(audit_log)
            await session.commit()

    except Exception as e:
        logger.error(f"Error logging audit event: {e}")
