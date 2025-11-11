"""
User Model for WATCHKEEPER

This module defines the User model for authentication and authorization.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Table, ForeignKey, Text
from sqlalchemy.orm import relationship
import enum

from src.core.database import Base


# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
)


class User(Base):
    """
    User model for authentication and authorization.

    Attributes:
        id: Unique identifier for the user
        username: Unique username
        email: Unique email address
        full_name: Full name of the user
        hashed_password: Bcrypt hashed password
        is_active: Whether the user account is active
        is_superuser: Whether the user has superuser privileges
        created_at: When the user was created
        updated_at: When the user was last updated
        last_login: When the user last logged in
        roles: List of roles assigned to the user
        audit_logs: Audit logs created by this user
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Additional info
    phone = Column(String(20), nullable=True)
    organization = Column(String(255), nullable=True)

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="assigned_to_user")

    def __repr__(self):
        """String representation of the user."""
        return f"<User(id={self.id}, username={self.username})>"
