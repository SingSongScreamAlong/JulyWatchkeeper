"""
Sitrep API Routes
Provides endpoints for requesting and retrieving situation reports
"""
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid
from fastapi import APIRouter, HTTPException, Path, Query, status
from pydantic import BaseModel, Field

from api.db import get_db_connection, logger

# Define the router
router = APIRouter(tags=["sitrep"])

# Define the models
class SitrepReport(BaseModel):
    id: str
    title: str
    summary: str
    details: str
    threatLevel: str
    recommendations: List[str]
    generatedAt: str

class SitrepResponse(BaseModel):
    id: str
    location: str
    coordinates: Tuple[float, float]
    reason: str
    requestedBy: str
    requestedAt: str
    status: str
    completedAt: Optional[str] = None
    report: Optional[SitrepReport] = None

class SitrepRequest(BaseModel):
    location: str
    reason: str
    coordinates: Optional[Tuple[float, float]] = None
    requestedBy: str
    timestamp: str

# Initialize the database table
def init_sitrep_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create sitreps table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sitreps (
            id TEXT PRIMARY KEY,
            location TEXT NOT NULL,
            coordinates TEXT NOT NULL,
            reason TEXT NOT NULL,
            requested_by TEXT NOT NULL,
            requested_at TEXT NOT NULL,
            status TEXT NOT NULL,
            completed_at TEXT,
            report_id TEXT,
            FOREIGN KEY (report_id) REFERENCES sitrep_reports(id)
        )
        ''')
        
        # Create sitrep_reports table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sitrep_reports (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            details TEXT NOT NULL,
            threat_level TEXT NOT NULL,
            recommendations TEXT NOT NULL,
            generated_at TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Sitrep tables initialized")
    except Exception as e:
        logger.error(f"Error initializing sitrep tables: {e}")

# Initialize tables
init_sitrep_table()

@router.post("/intelligence/sitrep", response_model=SitrepResponse)
async def request_sitrep(request: SitrepRequest):
    """
    Request a new situation report for a specific location
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate a unique ID for the sitrep
        sitrep_id = str(uuid.uuid4())
        
        # Store coordinates as a string (JSON)
        coordinates_str = str(request.coordinates) if request.coordinates else "[0, 0]"
        
        # Insert the sitrep request into the database
        cursor.execute(
            "INSERT INTO sitreps (id, location, coordinates, reason, requested_by, requested_at, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (sitrep_id, request.location, coordinates_str, request.reason, request.requestedBy, request.timestamp, "pending")
        )
        
        conn.commit()
        conn.close()
        
        # Return the created sitrep
        return SitrepResponse(
            id=sitrep_id,
            location=request.location,
            coordinates=request.coordinates or [0, 0],
            reason=request.reason,
            requestedBy=request.requestedBy,
            requestedAt=request.timestamp,
            status="pending"
        )
    except Exception as e:
        logger.error(f"Error requesting sitrep: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error requesting sitrep: {str(e)}"
        )

@router.get("/intelligence/sitrep/{sitrep_id}", response_model=SitrepResponse)
async def get_sitrep_by_id(sitrep_id: str = Path(..., title="The ID of the sitrep to retrieve")):
    """
    Get a specific situation report by ID
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query the sitrep
        cursor.execute("SELECT * FROM sitreps WHERE id = ?", (sitrep_id,))
        sitrep = cursor.fetchone()
        
        if not sitrep:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sitrep with ID {sitrep_id} not found"
            )
        
        # Convert to dictionary
        sitrep_dict = dict(sitrep)
        
        # Parse coordinates from string to tuple
        import ast
        coordinates = ast.literal_eval(sitrep_dict["coordinates"])
        
        # Check if there's an associated report
        report = None
        if sitrep_dict.get("report_id"):
            cursor.execute("SELECT * FROM sitrep_reports WHERE id = ?", (sitrep_dict["report_id"],))
            report_row = cursor.fetchone()
            if report_row:
                report_dict = dict(report_row)
                # Parse recommendations from string to list
                recommendations = report_dict["recommendations"].split(",")
                report = SitrepReport(
                    id=report_dict["id"],
                    title=report_dict["title"],
                    summary=report_dict["summary"],
                    details=report_dict["details"],
                    threatLevel=report_dict["threat_level"],
                    recommendations=recommendations,
                    generatedAt=report_dict["generated_at"]
                )
        
        conn.close()
        
        # Return the sitrep response
        return SitrepResponse(
            id=sitrep_dict["id"],
            location=sitrep_dict["location"],
            coordinates=coordinates,
            reason=sitrep_dict["reason"],
            requestedBy=sitrep_dict["requested_by"],
            requestedAt=sitrep_dict["requested_at"],
            status=sitrep_dict["status"],
            completedAt=sitrep_dict.get("completed_at"),
            report=report
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving sitrep {sitrep_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving sitrep: {str(e)}"
        )

@router.get("/intelligence/sitreps/all", response_model=List[SitrepResponse])
async def get_all_sitreps():
    """
    Get all situation reports
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query all sitreps
        cursor.execute("SELECT * FROM sitreps ORDER BY requested_at DESC")
        sitreps = cursor.fetchall()
        
        # Process results
        result = []
        for sitrep in sitreps:
            sitrep_dict = dict(sitrep)
            
            # Parse coordinates from string to tuple
            import ast
            coordinates = ast.literal_eval(sitrep_dict["coordinates"])
            
            # Check if there's an associated report
            report = None
            if sitrep_dict.get("report_id"):
                cursor.execute("SELECT * FROM sitrep_reports WHERE id = ?", (sitrep_dict["report_id"],))
                report_row = cursor.fetchone()
                if report_row:
                    report_dict = dict(report_row)
                    # Parse recommendations from string to list
                    recommendations = report_dict["recommendations"].split(",")
                    report = SitrepReport(
                        id=report_dict["id"],
                        title=report_dict["title"],
                        summary=report_dict["summary"],
                        details=report_dict["details"],
                        threatLevel=report_dict["threat_level"],
                        recommendations=recommendations,
                        generatedAt=report_dict["generated_at"]
                    )
            
            result.append(SitrepResponse(
                id=sitrep_dict["id"],
                location=sitrep_dict["location"],
                coordinates=coordinates,
                reason=sitrep_dict["reason"],
                requestedBy=sitrep_dict["requested_by"],
                requestedAt=sitrep_dict["requested_at"],
                status=sitrep_dict["status"],
                completedAt=sitrep_dict.get("completed_at"),
                report=report
            ))
        
        conn.close()
        return result
    except Exception as e:
        logger.error(f"Error retrieving all sitreps: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving all sitreps: {str(e)}"
        )
