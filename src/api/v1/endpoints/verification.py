"""
Verification endpoints for WATCHKEEPER API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.verification_service import VerificationService
from src.middleware.rbac import get_current_active_user

router = APIRouter(prefix="/verification", tags=["verification"])


@router.get("/source/{source_id}/reliability")
async def get_source_reliability(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Calculate and get reliability score for a source."""
    reliability = await VerificationService.calculate_source_reliability(db, source_id)

    return {
        "source_id": source_id,
        "reliability_score": reliability
    }


@router.get("/intelligence/{intelligence_id}/consensus")
async def find_consensus(
    intelligence_id: int,
    similarity_threshold: float = 0.7,
    time_window_hours: int = 24,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Find consensus among sources for an intelligence item."""
    result = await VerificationService.find_consensus(
        db,
        intelligence_id,
        similarity_threshold,
        time_window_hours
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return result


@router.get("/threat/{threat_id}/verify")
async def verify_threat(
    threat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Verify a threat using multiple sources."""
    result = await VerificationService.verify_threat_with_multiple_sources(db, threat_id)

    return result


@router.post("/sources/update-reliability")
async def update_all_source_reliability(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update reliability scores for all sources."""
    result = await VerificationService.update_all_source_reliabilities(db)

    return result
