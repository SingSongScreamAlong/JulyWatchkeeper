"""
Role and Permission management endpoints for WATCHKEEPER API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.core.database import get_db
from src.crud.crud_role import crud_role, crud_permission
from src.schemas.user import RoleCreate, RoleUpdate, RoleResponse, PermissionCreate, PermissionResponse
from src.middleware.rbac import get_current_superuser

router = APIRouter(prefix="/roles", tags=["roles"])
permission_router = APIRouter(prefix="/permissions", tags=["permissions"])


# Role endpoints
@router.get("/", response_model=List[RoleResponse])
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """List all roles."""
    roles = await crud_role.get_multi(db, skip=skip, limit=limit)
    return roles


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """Get a specific role."""
    role = await crud_role.get(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_in: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """Create a new role."""
    existing_role = await crud_role.get_by_name(db, role_in.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name already exists"
        )

    role = await crud_role.create(db, name=role_in.name, description=role_in.description)
    return role


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_in: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """Update a role."""
    role = await crud_role.get(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    if role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify system roles"
        )

    update_data = role_in.model_dump(exclude_unset=True)
    updated_role = await crud_role.update(db, role_id, **update_data)
    return updated_role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """Delete a role."""
    success = await crud_role.delete(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete role (may be a system role or not found)"
        )


@router.post("/{role_id}/permissions/{permission_id}", response_model=RoleResponse)
async def add_permission_to_role(
    role_id: int,
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """Add a permission to a role."""
    role = await crud_role.add_permission(db, role_id, permission_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role or permission not found"
        )
    return role


@router.delete("/{role_id}/permissions/{permission_id}", response_model=RoleResponse)
async def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """Remove a permission from a role."""
    role = await crud_role.remove_permission(db, role_id, permission_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role or permission not found"
        )
    return role


# Permission endpoints
@permission_router.get("/", response_model=List[PermissionResponse])
async def list_permissions(
    skip: int = 0,
    limit: int = 100,
    resource: str = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """List all permissions."""
    permissions = await crud_permission.get_multi(db, skip=skip, limit=limit, resource=resource)
    return permissions


@permission_router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """Get a specific permission."""
    permission = await crud_permission.get(db, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return permission


@permission_router.post("/", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_in: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """Create a new permission."""
    existing_permission = await crud_permission.get_by_name(db, permission_in.name)
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission name already exists"
        )

    permission = await crud_permission.create(
        db,
        name=permission_in.name,
        resource=permission_in.resource,
        action=permission_in.action,
        description=permission_in.description
    )
    return permission


@permission_router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """Delete a permission."""
    success = await crud_permission.delete(db, permission_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
