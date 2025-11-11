"""
Export Model for WATCHKEEPER

This module defines the Export model for tracking data exports.
"""

from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from src.core.database import Base


class ExportFormat(str, enum.Enum):
    """Enumeration of export formats."""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ExportStatus(str, enum.Enum):
    """Enumeration of export statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Export(Base):
    """
    Export model for tracking data exports.

    Attributes:
        id: Unique identifier for the export
        user_id: User who requested the export
        export_format: Format of the export
        status: Status of the export
        file_path: Path to the exported file
        file_size: Size of the exported file in bytes
        filters: JSON object with filters applied to the export
        row_count: Number of rows/items in the export
        created_at: When the export was requested
        completed_at: When the export was completed
        expires_at: When the export file will be deleted
        error_message: Error message if export failed
    """
    __tablename__ = "exports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='SET NULL'), nullable=True, index=True)

    # Export details
    export_format = Column(Enum(ExportFormat), nullable=False, index=True)
    status = Column(Enum(ExportStatus), nullable=False, default=ExportStatus.PENDING, index=True)

    # File information
    file_path = Column(String(500), nullable=True)
    file_size = Column(BigInteger, nullable=True)  # in bytes

    # Query details
    resource_type = Column(String(50), nullable=False)  # 'intelligence', 'threats', 'sources', etc.
    filters = Column(JSONB, nullable=True)
    row_count = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        """String representation of the export."""
        return f"<Export(id={self.id}, format={self.export_format}, status={self.status})>"
