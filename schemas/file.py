from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.file import FileType
from .user import UserPublic


class FileBase(BaseModel):
    original_name: str
    is_public: bool = False


class FileCreate(FileBase):
    pass


class FileUpdate(BaseModel):
    is_public: Optional[bool] = None


class FileResponse(FileBase):
    id: str
    filename: str
    file_path: str
    file_type: FileType
    mime_type: str
    file_size: int
    uploader_id: str
    uploader: Optional[UserPublic]
    download_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class FileList(BaseModel):
    files: list[FileResponse]
    total: int
    page: int
    limit: int


class FileUploadResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    file_type: FileType
    mime_type: str
    file_size: int
    url: str