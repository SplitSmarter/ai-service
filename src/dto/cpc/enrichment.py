from typing import List, Optional
from pydantic import BaseModel, Field

from src.dto.enums import UserTierEnum


class EnrichCPCRequest(BaseModel):
    cpc_code: str = Field(..., description="CPC code to enrich")
    user_text: Optional[str] = Field(None, description="Optional context or custom guidelines for this code")
    tier: UserTierEnum = Field(UserTierEnum.TIER_3, description="Model reasoning tier")



class EnrichCPCResponse(BaseModel):
    cpc_code: str = Field(..., description="CPC code or section identifier (e.g., '0' or '0111')")
    type: str = Field(..., description="Hierarchical level type: 'Section', 'Division', 'Group', 'Class', or 'Subclass'")
    official_title: str = Field(..., description="Official UN CPC standard title")
    keyword_icon: str = Field(..., description="Single clean conceptual keyword for looking up UI icons (e.g., 'Agriculture')")
    brand_names: List[str] = Field(default_factory=list, description="Top global or industry-leading brand examples associated with this CPC code")
    formatted_concatenation: str = Field(..., description="Comma-separated string of combined titles, synonyms, and brand names optimized for vector database embedding")
    description: str = Field(..., description="Detailed industry description explaining what products fall under this classification")