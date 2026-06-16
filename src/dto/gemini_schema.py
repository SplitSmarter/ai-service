from pydantic import BaseModel, Field
from typing import Optional, List
from src.dto.enums import MediaModalityEnum, FinishReasonEnum

class ModalityTokenCount(BaseModel):
    modality: MediaModalityEnum
    token_count: int

class GeminiUsageMetadata(BaseModel):
    candidates_token_count: int = Field(default=0)
    prompt_token_count: int = Field(default=0)
    thoughts_token_count: Optional[int] = Field(default=0, description="Tokens used for reasoning/thinking")
    total_token_count: int = Field(default=0)
    prompt_tokens_details: List[ModalityTokenCount] = Field(default_factory=list)

class ContentPart(BaseModel):
    text: str

class ResponseContent(BaseModel):
    parts: List[ContentPart]
    role: str = "model"

class ResponseCandidate(BaseModel):
    content: ResponseContent
    finish_reason: FinishReasonEnum | str
    index: int = 0

class SDKGeminiRawResponse(BaseModel):
    """Captures the full raw dump returned by client.models.generate_content"""
    response_id: Optional[str] = None
    model_version: str
    candidates: List[ResponseCandidate]
    usage_metadata: GeminiUsageMetadata