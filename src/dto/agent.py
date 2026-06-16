from pydantic import BaseModel, Field
from typing import Optional
from src.dto.enums import LLMProviderEnum, ExecutionTierEnum
from src.dto.gemini_schema import GeminiUsageMetadata

class GenerationRequest(BaseModel):
    provider: LLMProviderEnum = Field(..., description="Target model framework engine: 'gemini' or 'openai'")
    tier: ExecutionTierEnum = Field(default=ExecutionTierEnum.TIER_1, description="Performance execution tier: 1 to 4")
    prompt: str = Field(..., description="Context input payload instructions")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_output_tokens: Optional[int] = Field(default=1024, gt=0)

class GenerationResponseMetadata(BaseModel):
    model_processed: str
    key_identifier_used: str
    raw_usage: Optional[GeminiUsageMetadata] = None

class GenerationResponse(BaseModel):
    text: str = Field(..., description="The structural text returned back from the LLM execution path")
    tokens_used: int = Field(..., description="The final absolute counter metric value computed for Redis logging")
    meta: GenerationResponseMetadata