from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


class GenerationRequest(BaseModel):
    """Request model for all generation endpoints"""
    prompt: str = Field(..., description="Text prompt for generation")
    images: Optional[List[str]] = Field(default=None, description="List of image URLs")
    aspect_ratio: str = Field(default="1:1", description="Aspect ratio (e.g., '16:9', '4:3', '1:1')")

class AssetMeta(BaseModel):
    type: Optional[str] = None
    aspect: Optional[str] = None


class Asset(BaseModel):
    """Generated asset (image or video)"""
    kind: Literal["image", "video"]
    url: str
    video_id: Optional[int] = None  # Database ID for videos
    meta: Optional[AssetMeta] = None


class GenerationResponse(BaseModel):
    """Response model for all generation endpoints"""
    status: Literal["completed", "running", "failed"]
    assets: Optional[List[Asset]] = None
    job_set_id: Optional[str] = None
    provider: str = "higgsfield"
    input_echo: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FileUploadResponse(BaseModel):
    """Response for file upload"""
    id: str
    url: str
    expires_in_seconds: int


class VideoHistoryItem(BaseModel):
    """Single video generation history item"""
    id: int
    video_url: str
    prompt: str
    aspect_ratio: str
    job_set_id: str
    created_at: str
    
    class Config:
        from_attributes = True


class VideoHistoryResponse(BaseModel):
    """Response for video history"""
    total: int
    videos: List[VideoHistoryItem]


class MoodboardRequest(BaseModel):
    """Request for moodboard generation"""
    prompt: Optional[str] = None
    liked_pictures: Optional[List[str]] = None


class MoodboardResponse(BaseModel):
    """Response for moodboard generation"""
    images: List[str]
    total: int


class VideoDetailResponse(BaseModel):
    """Response for single video details"""
    id: int
    video_url: str
    prompt: str
    aspect_ratio: str
    job_set_id: str
    created_at: str
    
    class Config:
        from_attributes = True

