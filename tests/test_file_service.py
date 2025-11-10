"""Tests for File Service"""

import pytest
from app.services.file_service import FileService
from io import BytesIO
import os


class TestFileService:
    """Test file upload service"""

    @pytest.fixture
    def file_service(self, tmp_path):
        """Create file service with temp storage"""
        return FileService(storage_path=str(tmp_path))

    def test_is_allowed_file(self, file_service):
        """Test file type validation"""
        assert file_service.is_allowed_file('photo.jpg') == (True, 'images')
        assert file_service.is_allowed_file('document.pdf') == (True, 'documents')
        assert file_service.is_allowed_file('video.mp4') == (True, 'videos')
        assert file_service.is_allowed_file('malicious.exe') == (False, None)

    def test_sanitize_filename(self, file_service):
        """Test filename sanitization"""
        assert file_service.sanitize_filename('../etc/passwd') == 'passwd'
        assert file_service.sanitize_filename('normal file.jpg') == 'normal file.jpg'
        assert 'x' * 260 in file_service.sanitize_filename('x' * 300 + '.jpg')

    def test_calculate_file_hash(self, file_service):
        """Test file hashing"""
        content = b"test content"
        file = BytesIO(content)

        hash1 = file_service.calculate_file_hash(file)
        assert len(hash1) == 64  # SHA-256 hex length

        # Same content should produce same hash
        file2 = BytesIO(content)
        hash2 = file_service.calculate_file_hash(file2)
        assert hash1 == hash2

    @pytest.mark.asyncio
    async def test_upload_file(self, file_service):
        """Test file upload"""
        content = b"test image content"
        file = BytesIO(content)

        result = await file_service.upload_file(
            file=file,
            filename='test_photo.jpg',
            uploaded_by=1,
            related_entity='incident',
            related_id=123
        )

        assert result['success'] is True
        assert result['category'] == 'images'
        assert result['size_bytes'] == len(content)
        assert 'file_id' in result
        assert 'file_path' in result

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, file_service):
        """Test uploading invalid file type"""
        content = b"malicious content"
        file = BytesIO(content)

        result = await file_service.upload_file(
            file=file,
            filename='virus.exe',
            uploaded_by=1
        )

        assert result['success'] is False
        assert 'not allowed' in result['error']

    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, file_service):
        """Test uploading oversized file"""
        # Create file larger than max size
        content = b"x" * (file_service.MAX_FILE_SIZE + 1)
        file = BytesIO(content)

        result = await file_service.upload_file(
            file=file,
            filename='huge.jpg',
            uploaded_by=1
        )

        assert result['success'] is False
        assert 'too large' in result['error']
