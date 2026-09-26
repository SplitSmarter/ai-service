import json
import logging
from typing import Optional
from fastapi import HTTPException, status

from src.config.config import get_logger
from src.dto.llm.agent import GenerationResponse
from src.dto.enums import UserTierEnum
from src.dto.coicop.enrichment import EnrichCOICOPResponse
from src.services.central_ai_service import CentralAIService
from src.services.user_service import UserAIService

logger = get_logger()

class COICOPService:
    def __init__(self):
        self.logger = logger
        self.central_ai_service = CentralAIService()
        self.user_ai_service = UserAIService(self.central_ai_service)

    async def enrich_coicop_details(
        self,
        coicop_code: str,
        user_context: Optional[str],
        tier: UserTierEnum = UserTierEnum.TIER_2
    ) -> GenerationResponse:
        """
        Constructs the strict COICOP enrichment prompt and delegates execution to UserAIService.
        """
        try:
            prompt = self._build_coicop_prompt(coicop_code=coicop_code, user_context=user_context)
            self.logger.info(f"Routing COICOP enrichment prompt for code {coicop_code} to UserAIService.")

            response: GenerationResponse = await self.user_ai_service.generate_user_response(
                prompt=prompt,
                tier=tier,
                temperature=0.1
            )
            return response

        except HTTPException:
            raise
        except Exception as e:
            self.logger.exception(f"Failure inside COICOPService during enrichment for code {coicop_code}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to enrich COICOP code details with LLM."
            )

    def _build_coicop_prompt(self, coicop_code: str, user_context: Optional[str]) -> str:
        target_schema = json.dumps(EnrichCOICOPResponse.model_json_schema(), indent=2)

        return f"""
System Role: You are an expert UN COICOP (Classification of Individual Consumption According to Purpose, 2018 standard) taxonomist, data engineer, and consumer economist.
Your task is to generate rich metadata, vector-embedding text concatenations, icon keywords, and classification descriptions for a given COICOP code.

--- INPUT PARAMETERS ---
Target COICOP Code: {coicop_code}
Additional User Context / Hints: {user_context or 'None provided'}

--- INSTRUCTIONS & RULES ---
1. OFFICIAL DETAILS: Identify the official UN COICOP standard title and determine its structural hierarchy `type` ('Division', 'Group', 'Class', or 'Subclass').
2. VECTOR EMBEDDING STRING (`formatted_concatenation`): Build a comprehensive comma-separated string containing the title, common consumer synonyms, and related purchasing/grocery terms. This will be embedded into a vector database for semantic search.
3. ICON KEYWORD (`keyword_icon`): Provide a clean conceptual phrase suitable for UI icon retrieval libraries (e.g., 'Food Beverage', 'Housing Utilities', 'Transport', 'Healthcare').
4. DESCRIPTION: Write a professional summary explaining the boundaries and scope of household consumption items included under this COICOP classification.

--- TARGET JSON SCHEMA ---
Return valid JSON adhering strictly to the following EnrichCOICOPResponse schema:
{target_schema}
"""