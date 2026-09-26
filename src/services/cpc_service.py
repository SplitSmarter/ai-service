import json
import logging
from typing import Optional
from fastapi import HTTPException, status

from src.config.config import get_logger
from src.dto.llm.agent import GenerationResponse
from src.dto.enums import UserTierEnum
from src.dto.cpc.enrichment import EnrichCPCResponse
from src.services.central_ai_service import CentralAIService
from src.services.user_service import UserAIService

logger = get_logger()

class CPCService:
    def __init__(self):
        self.logger = logger
        self.central_ai_service = CentralAIService()
        self.user_ai_service = UserAIService(self.central_ai_service)

    async def enrich_cpc_details(
        self,
        cpc_code: str,
        user_context: Optional[str],
        tier: UserTierEnum = UserTierEnum.TIER_2
    ) -> GenerationResponse:
        """
        Constructs the strict CPC enrichment prompt and delegates execution to UserAIService.
        """
        try:
            prompt = self._build_cpc_prompt(cpc_code=cpc_code, user_context=user_context)
            self.logger.info(f"Routing CPC enrichment prompt for code {cpc_code} to UserAIService.")

            response: GenerationResponse = await self.user_ai_service.generate_user_response(
                prompt=prompt,
                tier=tier,
                temperature=0.1
            )
            return response

        except HTTPException:
            raise
        except Exception as e:
            self.logger.exception(f"Failure inside CPCService during enrichment for code {cpc_code}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to enrich CPC code details with LLM."
            )

    def _build_cpc_prompt(self, cpc_code: str, user_context: Optional[str]) -> str:
        target_schema = json.dumps(EnrichCPCResponse.model_json_schema(), indent=2)

        return f"""
System Role: You are an expert UN Central Product Classification (CPC v2.1) taxonomist, data engineer, and ontologist.
Your task is to generate rich metadata, vector-embedding text concatenations, top brand examples, and icon keywords for a given CPC classification code.

--- INPUT PARAMETERS ---
Target CPC Code: {cpc_code}
Additional User Context / Hints: {user_context or 'None provided'}

--- INSTRUCTIONS & RULES ---
1. OFFICIAL DETAILS: Identify the official UN CPC standard title and determine its structural hierarchy `type` ('Section', 'Division', 'Group', 'Class', or 'Subclass').
2. BRAND NAMES: Provide a list of 3-6 prominent global companies or well-known brands representing this classification.
3. ICON KEYWORD (`keyword_icon`): Provide a single, clean conceptual noun suitable for UI icon retrieval libraries (e.g., 'Agriculture', 'Technology', 'Healthcare', 'Apparel').
4. VECTOR EMBEDDING STRING (`formatted_concatenation`): Build a comprehensive comma-separated string containing the title, core synonyms, related concepts, and all brand names. This will be embedded into a vector database for semantic search.
5. DESCRIPTION: Write a professional summary explaining the exact boundaries and scope of products included under this CPC classification.

--- TARGET JSON SCHEMA ---
Return valid JSON adhering strictly to the following EnrichCPCResponse schema:
{target_schema}
"""