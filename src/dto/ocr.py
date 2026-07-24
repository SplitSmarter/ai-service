from typing import Optional, List
from pydantic import BaseModel, Field

from src.dto.enums import UserTierEnum, UserTierEnum, OCRProviderEnum


class OCRBlock(BaseModel):
    """Represents an individual text block parsed from an image layout."""
    text: str = Field(..., description="Extracted block text content")
    confidence: Optional[float] = Field(None, description="Detection confidence score if available")

class OCRRequest(BaseModel):
    image_bytes: Optional[bytes] = None
    image_path: Optional[str] = None
    tier: UserTierEnum = Field(
        default=UserTierEnum.TIER_1,
        description="Performance execution tier for OCR engine"
    )

class OCRResponse(BaseModel):
    full_text: str
    blocks: List[str]
    total_pages: int = 1