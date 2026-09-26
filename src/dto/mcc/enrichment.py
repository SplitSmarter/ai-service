from typing import Optional
from pydantic import BaseModel, Field

from src.dto.enums import UserTierEnum


class EnrichMCCRequest(BaseModel):
    mcc_code: str = Field(..., description="4-digit MCC code to enrich")
    user_text: Optional[str] = Field(None, description="Optional context or custom guidelines")
    tier: UserTierEnum = Field(UserTierEnum.TIER_3, description="Model reasoning tier")


class EnrichMCCResponse(BaseModel):
    code: str = Field(..., description="4-digit ISO 18245 MCC code (e.g., '5411')")
    description: str = Field(..., description="Standard industry description of the merchant category")
    group_category: Optional[str] = Field(None,
                                          description="Broader industry grouping (e.g., 'Groceries & Supermarkets')")
    localization_key: Optional[str] = Field(None, description="Localization key for UI text")
    default_coicop_code: Optional[str] = Field(None, description="Suggested standard COICOP code")
    default_cpc_code: Optional[str] = Field(None, description="Suggested standard CPC code")
    risk_tier: str = Field(default="LOW", description="Risk tier: 'LOW', 'MEDIUM', 'HIGH'")
    chargeback_threshold: float = Field(default=0.0100, description="Estimated chargeback threshold ratio")
    fraud_score_weight: float = Field(default=1.00, description="Weight multiplier for fraud scoring")
    irs_reportable: bool = Field(default=False, description="Whether transactions require IRS reporting")
    age_verification_mandatory: bool = Field(default=False,
                                             description="Whether age checks are mandatory (e.g., alcohol, tobacco)")
    is_sanction_restricted: bool = Field(default=False,
                                         description="Whether sector is heavily restricted or sanctioned")
    interchange_tier_label: Optional[str] = Field(None, description="Typical interchange qualification tier label")
    surcharge_eligible: bool = Field(default=True, description="Whether merchants can legally apply credit surcharges")
    rewards_multiplier_eligible: bool = Field(default=True, description="Whether eligible for card reward multipliers")
    icon_keyword: Optional[str] = Field(None, description="Suggested one keyword to identify the icon")
