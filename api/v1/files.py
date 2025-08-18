from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from models import File
from schemas.file import (
    FileResponse as FileResponseSchema,
    FileList,
    FileUpdate,
    FileUploadResponse
)
from services.file_service import FileService
from dependencies import (
    get_current_user,
    get_current_verified_user,
    PaginationParams
)
from models import User, FileType
from core.config import settings
from core.exceptions import (
    BadRequestException,
    FileNotFoundException,
    InsufficientPermissionsException
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    is_public: bool = Query(False, description="Make file publicly accessible"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Upload a new file"""
    uploaded_file = await FileService.upload_file(db, file, current_user, is_public)
    
    # Generate file URL
    file_url = f"{settings.API_V1_STR}/files/{uploaded_file.id}/download"
    
    return {
        "id": uploaded_file.id,
        "filename": uploaded_file.filename,
        "original_name": uploaded_file.original_name,
        "file_type": uploaded_file.file_type,
        "mime_type": uploaded_file.mime_type,
        "file_size": uploaded_file.file_size,
        "url": file_url
    }


@router.post("/upload-multiple", response_model=list[FileUploadResponse])
async def upload_multiple_files(
    files: list[UploadFile] = FastAPIFile(...),
    is_public: bool = Query(False, description="Make files publicly accessible"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Upload multiple files"""
    uploaded_files = []
    
    for file in files[:10]:  # Limit to 10 files at once
        try:
            uploaded_file = await FileService.upload_file(db, file, current_user, is_public)
            file_url = f"{settings.API_V1_STR}/files/{uploaded_file.id}/download"
            
            uploaded_files.append({
                "id": uploaded_file.id,
                "filename": uploaded_file.filename,
                "original_name": uploaded_file.original_name,
                "file_type": uploaded_file.file_type,
                "mime_type": uploaded_file.mime_type,
                "file_size": uploaded_file.file_size,
                "url": file_url
            })
        except Exception as e:
            # Continue with other files if one fails
            logger.warning(f"Failed to upload {file.filename}: {e}")
    
    return uploaded_files


@router.get("/", response_model=FileList)
async def get_files(
    pagination: PaginationParams = Depends(),
    file_type: Optional[FileType] = Query(None, description="Filter by file type"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's files"""
    files = FileService.get_user_files(
        db,
        current_user.id,
        skip=pagination.offset,
        limit=pagination.limit,
        file_type=file_type,
        is_public=is_public
    )
    
    total = FileService.count_user_files(
        db,
        current_user.id,
        file_type=file_type,
        is_public=is_public
    )
    
    # Add uploader info
    for file in files:
        file.uploader = current_user
    
    return {
        "files": files,
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit
    }


@router.get("/public", response_model=FileList)
async def get_public_files(
    pagination: PaginationParams = Depends(),
    file_type: Optional[FileType] = Query(None, description="Filter by file type"),
    db: Session = Depends(get_db)
):
    """Get all public files"""
    query = db.query(File).filter(File.is_public == True)
    
    if file_type:
        query = query.filter(File.file_type == file_type)
    
    total = query.count()
    files = query.order_by(File.created_at.desc()).offset(pagination.offset).limit(pagination.limit).all()
    
    return {
        "files": files,
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit
    }


@router.get("/stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get storage statistics for current user"""
    stats = FileService.get_storage_stats(db, current_user.id)
    return stats


@router.get("/{file_id}", response_model=FileResponseSchema)
async def get_file_info(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get file information"""
    file = FileService.get_file(db, file_id)
    
    # Check access permissions
    if not file.is_public:
        if file.uploader_id != current_user.id and current_user.role != "admin":
            raise InsufficientPermissionsException(detail="No access to this file")
    
    return file


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """Download a file"""
    # Try to get current user (optional for public files)
    current_user = None
    try:
        from dependencies import get_current_user_optional
        # This would need to be implemented as an optional dependency
        pass
    except:
        current_user = None
    
    file_path = FileService.get_file_path(db, file_id, current_user)
    file = FileService.get_file(db, file_id)
    
    return FileResponse(
        path=file_path,
        filename=file.original_name,
        media_type=file.mime_type
    )


@router.get("/{file_id}/thumbnail")
async def get_thumbnail(
    file_id: str,
    current_user: Optional[User] = None,
    db: Session = Depends(get_db)
):
    """Get thumbnail for image files"""
    # Try to get current user (optional for public files)
    try:
        from dependencies import get_current_user
        current_user = await get_current_user(db=db)
    except:
        current_user = None
    
    file = FileService.get_file(db, file_id)
    
    # Check if it's an image
    if file.file_type != FileType.IMAGE:
        raise BadRequestException(detail="Thumbnails only available for images")
    
    # Check access permissions
    if not file.is_public:
        if not current_user or (file.uploader_id != current_user.id and current_user.role != "admin"):
            raise InsufficientPermissionsException(detail="No access to this file")
    
    file_path = Path(file.file_path)
    thumbnail_path = file_path.parent / "thumbnails" / f"thumb_{file_path.name}"
    
    if not thumbnail_path.exists():
        raise FileNotFoundException(detail="Thumbnail not found")
    
    return FileResponse(
        path=thumbnail_path,
        media_type=file.mime_type
    )


@router.put("/{file_id}", response_model=FileResponseSchema)
async def update_file(
    file_id: str,
    file_update: FileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update file metadata"""
    updated_file = FileService.update_file(
        db,
        file_id,
        current_user,
        is_public=file_update.is_public
    )
    return updated_file


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a file"""
    FileService.delete_file(db, file_id, current_user)
    return {"message": "File deleted successfully"}