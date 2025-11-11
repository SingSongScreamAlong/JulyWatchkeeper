"""
Export endpoints for WATCHKEEPER API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os

from src.core.database import get_db
from src.models.export import Export, ExportStatus
from src.schemas.export import ExportCreate, ExportResponse
from src.middleware.rbac import get_current_active_user
from src.tasks.export_tasks import generate_export

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/", response_model=List[ExportResponse])
async def list_exports(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List user's export requests."""
    query = select(Export).where(Export.user_id == current_user.id)
    query = query.offset(skip).limit(limit).order_by(Export.created_at.desc())

    result = await db.execute(query)
    exports = result.scalars().all()
    return exports


@router.get("/{export_id}", response_model=ExportResponse)
async def get_export(
    export_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a specific export request."""
    result = await db.execute(
        select(Export).where(Export.id == export_id)
    )
    export = result.scalar_one_or_none()

    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )

    # Users can only access their own exports unless superuser
    if export.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return export


@router.post("/", response_model=ExportResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_export(
    export_in: ExportCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new export request (processed asynchronously)."""
    export = Export(
        user_id=current_user.id,
        export_format=export_in.export_format,
        resource_type=export_in.resource_type,
        filters=export_in.filters,
        status=ExportStatus.PENDING
    )

    db.add(export)
    await db.commit()
    await db.refresh(export)

    # Queue export generation
    generate_export.delay(export.id)

    return export


@router.get("/{export_id}/download")
async def download_export(
    export_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Download an export file."""
    result = await db.execute(
        select(Export).where(Export.id == export_id)
    )
    export = result.scalar_one_or_none()

    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )

    # Users can only download their own exports unless superuser
    if export.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    if export.status != ExportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export is not ready (status: {export.status})"
        )

    if not export.file_path or not os.path.exists(export.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )

    # Determine media type
    media_types = {
        "pdf": "application/pdf",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "json": "application/json"
    }
    media_type = media_types.get(export.export_format.value, "application/octet-stream")

    return FileResponse(
        export.file_path,
        media_type=media_type,
        filename=os.path.basename(export.file_path)
    )


@router.delete("/{export_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_export(
    export_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete an export and its file."""
    result = await db.execute(
        select(Export).where(Export.id == export_id)
    )
    export = result.scalar_one_or_none()

    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )

    # Users can only delete their own exports unless superuser
    if export.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Delete file if it exists
    if export.file_path and os.path.exists(export.file_path):
        os.remove(export.file_path)

    await db.delete(export)
    await db.commit()
