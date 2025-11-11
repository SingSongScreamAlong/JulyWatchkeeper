"""
CRUD operations for Role and Permission models
"""

from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.role import Role, Permission


class CRUDRole:
    """CRUD operations for roles."""

    @staticmethod
    async def get(db: AsyncSession, role_id: int) -> Optional[Role]:
        """Get a role by ID."""
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[Role]:
        """Get a role by name."""
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.name == name)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_multi(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Role]:
        """Get multiple roles."""
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession,
        name: str,
        description: Optional[str] = None,
        is_system_role: bool = False
    ) -> Role:
        """Create a new role."""
        role = Role(
            name=name,
            description=description,
            is_system_role=is_system_role
        )

        db.add(role)
        await db.commit()
        await db.refresh(role)
        return role

    @staticmethod
    async def update(
        db: AsyncSession,
        role_id: int,
        **kwargs
    ) -> Optional[Role]:
        """Update a role."""
        await db.execute(
            update(Role)
            .where(Role.id == role_id)
            .values(**kwargs)
        )
        await db.commit()

        return await CRUDRole.get(db, role_id)

    @staticmethod
    async def delete(db: AsyncSession, role_id: int) -> bool:
        """Delete a role (only if not a system role)."""
        # Check if it's a system role first
        role = await CRUDRole.get(db, role_id)
        if role and role.is_system_role:
            return False

        result = await db.execute(
            delete(Role).where(Role.id == role_id)
        )
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def add_permission(
        db: AsyncSession,
        role_id: int,
        permission_id: int
    ) -> Optional[Role]:
        """Add a permission to a role."""
        role = await CRUDRole.get(db, role_id)
        if not role:
            return None

        perm_result = await db.execute(
            select(Permission).where(Permission.id == permission_id)
        )
        permission = perm_result.scalar_one_or_none()
        if not permission:
            return None

        if permission not in role.permissions:
            role.permissions.append(permission)
            await db.commit()
            await db.refresh(role)

        return role

    @staticmethod
    async def remove_permission(
        db: AsyncSession,
        role_id: int,
        permission_id: int
    ) -> Optional[Role]:
        """Remove a permission from a role."""
        role = await CRUDRole.get(db, role_id)
        if not role:
            return None

        perm_result = await db.execute(
            select(Permission).where(Permission.id == permission_id)
        )
        permission = perm_result.scalar_one_or_none()
        if not permission:
            return None

        if permission in role.permissions:
            role.permissions.remove(permission)
            await db.commit()
            await db.refresh(role)

        return role


class CRUDPermission:
    """CRUD operations for permissions."""

    @staticmethod
    async def get(db: AsyncSession, permission_id: int) -> Optional[Permission]:
        """Get a permission by ID."""
        result = await db.execute(
            select(Permission).where(Permission.id == permission_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[Permission]:
        """Get a permission by name."""
        result = await db.execute(
            select(Permission).where(Permission.name == name)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_multi(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        resource: Optional[str] = None
    ) -> List[Permission]:
        """Get multiple permissions."""
        query = select(Permission)

        if resource:
            query = query.where(Permission.resource == resource)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession,
        name: str,
        resource: str,
        action: str,
        description: Optional[str] = None
    ) -> Permission:
        """Create a new permission."""
        permission = Permission(
            name=name,
            resource=resource,
            action=action,
            description=description
        )

        db.add(permission)
        await db.commit()
        await db.refresh(permission)
        return permission

    @staticmethod
    async def delete(db: AsyncSession, permission_id: int) -> bool:
        """Delete a permission."""
        result = await db.execute(
            delete(Permission).where(Permission.id == permission_id)
        )
        await db.commit()
        return result.rowcount > 0


crud_role = CRUDRole()
crud_permission = CRUDPermission()
