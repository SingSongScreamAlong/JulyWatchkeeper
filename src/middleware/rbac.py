"""
Role-Based Access Control (RBAC) Middleware for WATCHKEEPER

This module implements RBAC for API endpoints.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List
import os

from src.core.database import get_db
from src.crud.crud_user import crud_user

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user from JWT token.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await crud_user.get_by_username(db, username=username)
    if user is None:
        raise credentials_exception

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    return user


async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    Get current active user.

    Args:
        current_user: User from token

    Returns:
        Active user object

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(current_user = Depends(get_current_user)):
    """
    Get current superuser.

    Args:
        current_user: User from token

    Returns:
        Superuser object

    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


class PermissionChecker:
    """Dependency to check if user has required permissions."""

    def __init__(self, required_permissions: List[str]):
        """
        Initialize permission checker.

        Args:
            required_permissions: List of required permission names
        """
        self.required_permissions = required_permissions

    async def __call__(self, current_user = Depends(get_current_active_user)):
        """
        Check if user has required permissions.

        Args:
            current_user: Current active user

        Returns:
            User object if authorized

        Raises:
            HTTPException: If user lacks required permissions
        """
        # Superusers have all permissions
        if current_user.is_superuser:
            return current_user

        # Get user's permissions from their roles
        user_permissions = set()
        for role in current_user.roles:
            for permission in role.permissions:
                user_permissions.add(permission.name)

        # Check if user has all required permissions
        missing_permissions = set(self.required_permissions) - user_permissions

        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing_permissions)}"
            )

        return current_user


def require_permissions(*permissions: str):
    """
    Decorator to require specific permissions.

    Usage:
        @router.get("/endpoint")
        async def endpoint(user = Depends(require_permissions("intelligence:read"))):
            ...

    Args:
        permissions: Permission names required

    Returns:
        Dependency that checks permissions
    """
    return Depends(PermissionChecker(list(permissions)))
