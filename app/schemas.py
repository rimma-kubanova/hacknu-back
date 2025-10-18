from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


class GenerationOptions(BaseModel):
    """Options for generation requests"""
    mode: Optional[Literal["device", "billboard", "plain"]] = None
    animate: Optional[bool] = False
    count: Optional[int] = 1
    duration: Optional[int] = 8
    model_hint: Optional[Literal["fast", "polish"]] = "fast"


class GenerationRequest(BaseModel):
    """Request model for all generation endpoints"""
    prompt: str = Field(..., description="Text prompt for generation")
    images: Optional[List[str]] = Field(default=None, description="List of image URLs")
    aspect_ratio: str = Field(default="1:1", description="Aspect ratio (e.g., '16:9', '4:3', '1:1')")
    options: Optional[GenerationOptions] = None


class AssetMeta(BaseModel):
    """Metadata for generated assets"""
    type: Optional[str] = None
    w: Optional[int] = None
    h: Optional[int] = None
    dur: Optional[int] = None
    aspect: Optional[str] = None


class Asset(BaseModel):
    """Generated asset (image or video)"""
    kind: Literal["image", "video"]
    url: str
    meta: Optional[AssetMeta] = None


class GenerationResponse(BaseModel):
    """Response model for all generation endpoints"""
    status: Literal["completed", "running", "failed"]
    assets: Optional[List[Asset]] = None
    credits_used: Optional[int] = None
    job_set_id: Optional[str] = None
    provider: str = "higgsfield"
    input_echo: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    poll_after_ms: Optional[int] = None


class FileUploadResponse(BaseModel):
    """Response for file upload"""
    id: str
    url: str
    expires_in_seconds: int

