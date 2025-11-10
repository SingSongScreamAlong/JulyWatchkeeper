"""File Upload and Storage Service

Handles secure file uploads for incident attachments, personnel photos, etc.
"""

import os
import uuid
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional, BinaryIO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FileService:
    """Manages file uploads and storage"""

    ALLOWED_EXTENSIONS = {
        'images': {'.jpg', '.jpeg', '.png', '.gif', '.webp'},
        'documents': {'.pdf', '.doc', '.docx', '.txt', '.odt'},
        'videos': {'.mp4', '.mov', '.avi', '.webm'},
        'audio': {'.mp3', '.wav', '.ogg', '.m4a'}
    }

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    def __init__(self, storage_path: str = None, use_s3: bool = False):
        """Initialize file service

        Args:
            storage_path: Local filesystem path for file storage
            use_s3: Whether to use S3 for storage (not yet implemented)
        """
        self.storage_path = storage_path or os.getenv('FILE_STORAGE_PATH', '/var/watchkeeper/uploads')
        self.use_s3 = use_s3

        # Create storage directories
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
        for category in self.ALLOWED_EXTENSIONS.keys():
            Path(self.storage_path) / category).mkdir(exist_ok=True)

    def is_allowed_file(self, filename: str) -> tuple[bool, Optional[str]]:
        """Check if file extension is allowed

        Returns:
            (is_allowed, category) tuple
        """
        ext = Path(filename).suffix.lower()

        for category, extensions in self.ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return True, category

        return False, None

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal"""
        # Get just the filename, no path components
        filename = os.path.basename(filename)

        # Remove any non-alphanumeric characters except dots and dashes
        import re
        filename = re.sub(r'[^\w\s.-]', '', filename)

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext

        return filename

    def calculate_file_hash(self, file: BinaryIO) -> str:
        """Calculate SHA-256 hash of file"""
        hasher = hashlib.sha256()

        # Read file in chunks
        file.seek(0)
        while True:
            chunk = file.read(8192)
            if not chunk:
                break
            hasher.update(chunk)

        file.seek(0)  # Reset file pointer
        return hasher.hexdigest()

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        uploaded_by: int,
        related_entity: str = None,
        related_id: int = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Upload and store a file

        Args:
            file: File-like object
            filename: Original filename
            uploaded_by: User ID who uploaded
            related_entity: Entity type (incident, personnel, etc.)
            related_id: Entity ID
            metadata: Additional metadata

        Returns:
            Dict with file information
        """
        try:
            # Validate file
            is_allowed, category = self.is_allowed_file(filename)
            if not is_allowed:
                raise ValueError(f"File type not allowed: {filename}")

            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning

            if file_size > self.MAX_FILE_SIZE:
                raise ValueError(f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE})")

            # Sanitize filename
            safe_filename = self.sanitize_filename(filename)

            # Generate unique filename
            unique_id = uuid.uuid4().hex
            timestamp = datetime.utcnow().strftime('%Y%m%d')
            ext = Path(safe_filename).suffix
            stored_filename = f"{timestamp}_{unique_id}{ext}"

            # Calculate file hash for deduplication
            file_hash = self.calculate_file_hash(file)

            # Determine storage path
            storage_dir = Path(self.storage_path) / category
            file_path = storage_dir / stored_filename

            # Save file
            with open(file_path, 'wb') as f:
                file.seek(0)
                f.write(file.read())

            # Get MIME type
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

            # Generate thumbnail for images
            thumbnail_path = None
            if category == 'images':
                thumbnail_path = await self._generate_thumbnail(file_path)

            logger.info(f"File uploaded: {stored_filename} ({file_size} bytes)")

            return {
                'success': True,
                'file_id': unique_id,
                'original_filename': safe_filename,
                'stored_filename': stored_filename,
                'file_path': str(file_path),
                'category': category,
                'mime_type': mime_type,
                'size_bytes': file_size,
                'file_hash': file_hash,
                'thumbnail_path': thumbnail_path,
                'uploaded_by': uploaded_by,
                'uploaded_at': datetime.utcnow().isoformat(),
                'related_entity': related_entity,
                'related_id': related_id,
                'metadata': metadata or {}
            }

        except Exception as e:
            logger.error(f"Error uploading file {filename}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _generate_thumbnail(self, image_path: Path, size: tuple = (300, 300)) -> Optional[str]:
        """Generate thumbnail for image"""
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                img.thumbnail(size)

                # Save thumbnail
                thumbnail_dir = image_path.parent / 'thumbnails'
                thumbnail_dir.mkdir(exist_ok=True)

                thumbnail_path = thumbnail_dir / f"thumb_{image_path.name}"
                img.save(thumbnail_path, optimize=True, quality=85)

                logger.info(f"Thumbnail generated: {thumbnail_path}")
                return str(thumbnail_path)

        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return None

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage"""
        try:
            path = Path(file_path)

            if not path.exists():
                logger.warning(f"File not found: {file_path}")
                return False

            # Delete main file
            path.unlink()

            # Delete thumbnail if exists
            thumbnail_path = path.parent / 'thumbnails' / f"thumb_{path.name}"
            if thumbnail_path.exists():
                thumbnail_path.unlink()

            logger.info(f"File deleted: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False

    def get_file_url(self, stored_filename: str, category: str) -> str:
        """Get URL for accessing file"""
        # For local files, return relative path
        # In production, this would return S3 URL or CDN URL
        return f"/uploads/{category}/{stored_filename}"

    async def scan_file_for_viruses(self, file_path: str) -> Dict[str, Any]:
        """Scan file for viruses using ClamAV (optional)"""
        try:
            import subprocess

            # Check if ClamAV is installed
            result = subprocess.run(
                ['clamscan', '--no-summary', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return {'clean': True, 'details': 'No threats found'}
            else:
                return {
                    'clean': False,
                    'details': result.stdout,
                    'threat_detected': True
                }

        except FileNotFoundError:
            logger.warning("ClamAV not installed, skipping virus scan")
            return {'clean': True, 'details': 'Virus scanning not available'}
        except Exception as e:
            logger.error(f"Error scanning file: {e}")
            return {'clean': None, 'error': str(e)}


# Singleton instance
_file_service = None


def get_file_service() -> FileService:
    """Get singleton file service instance"""
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service
