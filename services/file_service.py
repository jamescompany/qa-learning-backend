import os
import shutil
import mimetypes
from typing import Optional, List, BinaryIO
from pathlib import Path
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from fastapi import UploadFile
from PIL import Image
from core.config import settings
from core.exceptions import (
    FileNotFoundException,
    FileSizeException,
    FileTypeException,
    BadRequestException,
    InsufficientPermissionsException
)
from models import File, FileType, User
import logging

logger = logging.getLogger(__name__)


class FileService:
    @staticmethod
    def get_file_type(mime_type: str) -> FileType:
        """Determine file type from MIME type"""
        if mime_type.startswith("image/"):
            return FileType.IMAGE
        elif mime_type in ["application/pdf", "application/msword", 
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                          "text/plain"]:
            return FileType.DOCUMENT
        elif mime_type.startswith("video/"):
            return FileType.VIDEO
        elif mime_type.startswith("audio/"):
            return FileType.AUDIO
        else:
            return FileType.OTHER
    
    @staticmethod
    def validate_file(file: UploadFile) -> tuple[bool, str]:
        """Validate uploaded file"""
        # Check file size
        if file.size and file.size > settings.MAX_UPLOAD_SIZE:
            return False, f"File size exceeds maximum allowed size ({settings.MAX_UPLOAD_SIZE} bytes)"
        
        # Check file extension
        file_extension = Path(file.filename).suffix.lower().lstrip(".")
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            return False, f"File type .{file_extension} not allowed"
        
        return True, "File is valid"
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Generate unique filename while preserving extension"""
        file_extension = Path(original_filename).suffix
        unique_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{unique_id}{file_extension}"
    
    @staticmethod
    def create_upload_directory() -> Path:
        """Create upload directory if it doesn't exist"""
        upload_path = Path(settings.UPLOAD_DIR)
        
        # Create subdirectories by year/month
        now = datetime.utcnow()
        year_month = now.strftime("%Y/%m")
        full_path = upload_path / year_month
        
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path
    
    @staticmethod
    async def upload_file(
        db: Session,
        file: UploadFile,
        user: User,
        is_public: bool = False
    ) -> File:
        """Upload a file and save metadata to database"""
        # Validate file
        is_valid, message = FileService.validate_file(file)
        if not is_valid:
            raise FileTypeException(detail=message)
        
        # Generate unique filename
        unique_filename = FileService.generate_unique_filename(file.filename)
        
        # Create upload directory
        upload_dir = FileService.create_upload_directory()
        file_path = upload_dir / unique_filename
        
        try:
            # Save file to disk
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file info
            file_stats = os.stat(file_path)
            mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
            file_type = FileService.get_file_type(mime_type)
            
            # If it's an image, create thumbnail
            if file_type == FileType.IMAGE:
                try:
                    FileService.create_thumbnail(file_path)
                except Exception as e:
                    logger.warning(f"Failed to create thumbnail: {e}")
            
            # Save to database
            db_file = File(
                filename=unique_filename,
                original_name=file.filename,
                file_path=str(file_path.relative_to(Path.cwd())),
                file_type=file_type,
                mime_type=mime_type,
                file_size=file_stats.st_size,
                uploader_id=user.id,
                is_public=is_public
            )
            
            db.add(db_file)
            db.commit()
            db.refresh(db_file)
            
            logger.info(f"File uploaded: {file.filename} -> {unique_filename}")
            return db_file
            
        except Exception as e:
            # Clean up file if database save fails
            if file_path.exists():
                file_path.unlink()
            logger.error(f"File upload failed: {e}")
            raise BadRequestException(detail=f"File upload failed: {str(e)}")
    
    @staticmethod
    def create_thumbnail(image_path: Path, size: tuple = (200, 200)) -> Path:
        """Create thumbnail for image files"""
        thumbnail_dir = image_path.parent / "thumbnails"
        thumbnail_dir.mkdir(exist_ok=True)
        
        thumbnail_path = thumbnail_dir / f"thumb_{image_path.name}"
        
        with Image.open(image_path) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(thumbnail_path)
        
        return thumbnail_path
    
    @staticmethod
    def get_file(db: Session, file_id: str) -> File:
        """Get file metadata by ID"""
        file = db.query(File).filter(File.id == file_id).first()
        if not file:
            raise FileNotFoundException()
        return file
    
    @staticmethod
    def get_file_path(db: Session, file_id: str, user: Optional[User] = None) -> Path:
        """Get file path for download"""
        file = FileService.get_file(db, file_id)
        
        # Check access permissions
        if not file.is_public:
            if not user or (file.uploader_id != user.id and user.role != "admin"):
                raise InsufficientPermissionsException(detail="No access to this file")
        
        file_path = Path(file.file_path)
        if not file_path.exists():
            raise FileNotFoundException(detail="File not found on disk")
        
        # Increment download count
        file.download_count += 1
        db.commit()
        
        return file_path
    
    @staticmethod
    def get_user_files(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        file_type: Optional[FileType] = None,
        is_public: Optional[bool] = None
    ) -> List[File]:
        """Get files uploaded by a user"""
        query = db.query(File).filter(File.uploader_id == user_id)
        
        if file_type:
            query = query.filter(File.file_type == file_type)
        
        if is_public is not None:
            query = query.filter(File.is_public == is_public)
        
        return query.order_by(File.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_user_files(
        db: Session,
        user_id: str,
        file_type: Optional[FileType] = None,
        is_public: Optional[bool] = None
    ) -> int:
        """Count files uploaded by a user"""
        query = db.query(File).filter(File.uploader_id == user_id)
        
        if file_type:
            query = query.filter(File.file_type == file_type)
        
        if is_public is not None:
            query = query.filter(File.is_public == is_public)
        
        return query.count()
    
    @staticmethod
    def update_file(
        db: Session,
        file_id: str,
        user: User,
        is_public: Optional[bool] = None
    ) -> File:
        """Update file metadata"""
        file = FileService.get_file(db, file_id)
        
        # Check permissions
        if file.uploader_id != user.id and user.role != "admin":
            raise InsufficientPermissionsException()
        
        if is_public is not None:
            file.is_public = is_public
        
        db.commit()
        db.refresh(file)
        
        return file
    
    @staticmethod
    def delete_file(db: Session, file_id: str, user: User) -> bool:
        """Delete file from database and disk"""
        file = FileService.get_file(db, file_id)
        
        # Check permissions
        if file.uploader_id != user.id and user.role != "admin":
            raise InsufficientPermissionsException()
        
        # Delete file from disk
        file_path = Path(file.file_path)
        if file_path.exists():
            file_path.unlink()
            
            # Delete thumbnail if exists
            if file.file_type == FileType.IMAGE:
                thumbnail_path = file_path.parent / "thumbnails" / f"thumb_{file_path.name}"
                if thumbnail_path.exists():
                    thumbnail_path.unlink()
        
        # Delete from database
        db.delete(file)
        db.commit()
        
        logger.info(f"File deleted: {file.original_name}")
        return True
    
    @staticmethod
    def get_storage_stats(db: Session, user_id: str) -> dict:
        """Get storage statistics for a user"""
        files = db.query(File).filter(File.uploader_id == user_id).all()
        
        total_size = sum(f.file_size for f in files)
        file_count = len(files)
        
        type_stats = {}
        for file_type in FileType:
            type_files = [f for f in files if f.file_type == file_type]
            type_stats[file_type.value] = {
                "count": len(type_files),
                "size": sum(f.file_size for f in type_files)
            }
        
        return {
            "total_size": total_size,
            "file_count": file_count,
            "by_type": type_stats
        }