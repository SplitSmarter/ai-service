import json
import logging
from typing import Optional
from fastapi import HTTPException, status

from src.config.config import get_logger
from src.dto.llm.agent import GenerationResponse
from src.dto.enums import UserTierEnum
from src.dto.mcc.enrichment import EnrichMCCResponse
from src.services.central_ai_service import CentralAIService
from src.services.user_service import UserAIService

logger = get_logger()

class MCCService:
    def __init__(self):
        self.logger = logger
        self.central_ai_service = CentralAIService()
        self.user_ai_service = UserAIService(self.central_ai_service)

    async def enrich_mcc_details(
        self,
        mcc_code: str,
        user_context: Optional[str],
        tier: UserTierEnum = UserTierEnum.TIER_2
    ) -> GenerationResponse:
        """
        Constructs the strict MCC enrichment prompt and delegates execution to UserAIService.
        """
        try:
            prompt = self._build_mcc_prompt(mcc_code=mcc_code, user_context=user_context)
            self.logger.info(f"Routing MCC enrichment prompt for code {mcc_code} to UserAIService.")

            response: GenerationResponse = await self.user_ai_service.generate_user_response(
                prompt=prompt,
                tier=tier,
                temperature=0.1
            )
            return response

        except HTTPException:
            raise
        except Exception as e:
            self.logger.exception(f"Failure inside MCCService during enrichment for code {mcc_code}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to enrich merchant category code details with LLM."
            )

    def _build_mcc_prompt(self, mcc_code: str, user_context: Optional[str]) -> str:
        target_schema = json.dumps(EnrichMCCResponse.model_json_schema(), indent=2)

        return f"""
System Role: You are an expert financial compliance officer, card scheme network specialist (Visa/Mastercard ISO 18245), and risk analyst.
Your task is to populate complete master database record attributes for a given Merchant Category Code (MCC).

--- INPUT PARAMETERS ---
Target MCC Code: {mcc_code}
Additional User Context / Hints: {user_context or 'None provided'}

--- INSTRUCTIONS & RULES ---
1. CODE & DESCRIPTION: Provide the exact official ISO 18245 description for code '{mcc_code}'.
2. COMPLIANCE & RISK:
   - Determine `risk_tier` ('LOW', 'MEDIUM', 'HIGH').
   - Set `age_verification_mandatory` to true if the category involves age-restricted goods (e.g., alcohol, gambling, adult, tobacco).
   - Set `irs_reportable` true if payments fall under strict tax-reporting thresholds (e.g., service networks, digital goods).
3. FINANCIAL & REWARDS: Set realistic `chargeback_threshold` (e.g., 0.0100) and `fraud_score_weight`. Check `surcharge_eligible` and `rewards_multiplier_eligible` conventions.
4. TAXONOMY MAPPING: Suggest compatible `default_coicop_code` and `default_cpc_code` values if applicable.

--- TARGET JSON SCHEMA ---
Return valid JSON adhering strictly to the following EnrichMCCResponse schema:
{target_schema}
"""