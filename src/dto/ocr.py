from typing import Optional, List
from pydantic import BaseModel, Field


class OCRBlock(BaseModel):
    """Represents an individual text block parsed from an image layout."""
    text: str = Field(..., description="Extracted block text content")
    confidence: Optional[float] = Field(None, description="Detection confidence score if available")


class OCRResponse(BaseModel):
    """Unified response containing full extracted text and structured layout blocks."""
    full_text: str = Field(..., description="Complete text reconstructed from image")
    blocks: List[str] = Field(default_factory=list, description="Text broken down by visual layout blocks")
    total_pages: int = Field(default=1, description="Number of pages processed")


class OCRRequest(BaseModel):
    """Request DTO to trigger OCR processing."""
    image_path: Optional[str] = None
    image_bytes: Optional[bytes] = None