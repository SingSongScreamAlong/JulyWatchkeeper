"""
Role and Permission Models for WATCHKEEPER RBAC

This module defines Role and Permission models for role-based access control.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Table, ForeignKey, Text
from sqlalchemy.orm import relationship

from src.core.database import Base
from src.models.user import user_roles


# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
)


class Role(Base):
    """
    Role model for RBAC.

    Attributes:
        id: Unique identifier for the role
        name: Unique name of the role (e.g., 'admin', 'analyst', 'viewer')
        description: Description of the role
        is_system_role: Whether this is a system role (cannot be deleted)
        created_at: When the role was created
        updated_at: When the role was last updated
        users: Users assigned to this role
        permissions: Permissions granted to this role
    """
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

    def __repr__(self):
        """String representation of the role."""
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(Base):
    """
    Permission model for RBAC.

    Attributes:
        id: Unique identifier for the permission
        name: Unique name of the permission (e.g., 'intelligence:read', 'threats:create')
        resource: Resource this permission applies to (e.g., 'intelligence', 'threats', 'users')
        action: Action allowed (e.g., 'read', 'create', 'update', 'delete')
        description: Description of the permission
        created_at: When the permission was created
        roles: Roles that have this permission
    """
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    resource = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

    def __repr__(self):
        """String representation of the permission."""
        return f"<Permission(id={self.id}, name={self.name})>"
