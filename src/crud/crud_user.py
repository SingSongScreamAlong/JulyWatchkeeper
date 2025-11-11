"""
CRUD operations for User model
"""

from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from passlib.context import CryptContext

from src.models.user import User
from src.models.role import Role

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CRUDUser:
    """CRUD operations for users."""

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    async def get(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get a user by username."""
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.username == username)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get a user by email."""
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_multi(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """Get multiple users."""
        query = select(User).options(selectinload(User.roles))

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        is_superuser: bool = False,
        is_active: bool = True,
        phone: Optional[str] = None,
        organization: Optional[str] = None
    ) -> User:
        """Create a new user."""
        hashed_password = CRUDUser.get_password_hash(password)

        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_superuser=is_superuser,
            is_active=is_active,
            phone=phone,
            organization=organization
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update(
        db: AsyncSession,
        user_id: int,
        **kwargs
    ) -> Optional[User]:
        """Update a user."""
        # Hash password if provided
        if "password" in kwargs:
            kwargs["hashed_password"] = CRUDUser.get_password_hash(kwargs.pop("password"))

        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**kwargs)
        )
        await db.commit()

        return await CRUDUser.get(db, user_id)

    @staticmethod
    async def delete(db: AsyncSession, user_id: int) -> bool:
        """Delete a user."""
        result = await db.execute(
            delete(User).where(User.id == user_id)
        )
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        username: str,
        password: str
    ) -> Optional[User]:
        """Authenticate a user."""
        user = await CRUDUser.get_by_username(db, username)
        if not user:
            return None
        if not CRUDUser.verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def add_role(
        db: AsyncSession,
        user_id: int,
        role_id: int
    ) -> Optional[User]:
        """Add a role to a user."""
        user = await CRUDUser.get(db, user_id)
        if not user:
            return None

        role_result = await db.execute(
            select(Role).where(Role.id == role_id)
        )
        role = role_result.scalar_one_or_none()
        if not role:
            return None

        if role not in user.roles:
            user.roles.append(role)
            await db.commit()
            await db.refresh(user)

        return user

    @staticmethod
    async def remove_role(
        db: AsyncSession,
        user_id: int,
        role_id: int
    ) -> Optional[User]:
        """Remove a role from a user."""
        user = await CRUDUser.get(db, user_id)
        if not user:
            return None

        role_result = await db.execute(
            select(Role).where(Role.id == role_id)
        )
        role = role_result.scalar_one_or_none()
        if not role:
            return None

        if role in user.roles:
            user.roles.remove(role)
            await db.commit()
            await db.refresh(user)

        return user


crud_user = CRUDUser()
