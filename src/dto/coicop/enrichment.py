from typing import Optional
from pydantic import BaseModel, Field
from src.dto.enums import UserTierEnum


class EnrichCOICOPRequest(BaseModel):
    coicop_code: str = Field(..., description="COICOP code to enrich (e.g., '01' or '01.1.1')")
    user_text: Optional[str] = Field(None, description="Optional context or custom guidelines for this code")
    tier: UserTierEnum = Field(UserTierEnum.TIER_3, description="Model reasoning tier")


class EnrichCOICOPResponse(BaseModel):
    coicop_code: str = Field(..., description="COICOP code or division/group identifier (e.g., '01' or '01.1')")
    type: str = Field(..., description="Hierarchical level type: 'Division', 'Group', 'Class', or 'Subclass'")
    official_title: str = Field(..., description="Official UN COICOP standard title")
    formatted_concatenation: str = Field(...,
                                         description="Comma-separated string of combined titles, synonyms, and consumer terms optimized for vector database embedding")
    keyword_icon: str = Field(...,
                              description="Single clean conceptual keyword phrase for looking up UI icons (e.g., 'Food Beverage')")
    description: str = Field(...,
                             description="Detailed description explaining what consumption items fall under this COICOP classification")
