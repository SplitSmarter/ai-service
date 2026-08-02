import json
import logging
from typing import List
from fastapi import HTTPException, status

from src.config.config import get_logger
from src.dto.catalog.enrichment import (
    EnrichProductsBatchRequest,
    EnrichProductsBatchResponse,
)
from src.dto.enums import UserTierEnum
from src.dto.llm.agent import GenerationResponse
from src.services.central_ai_service import CentralAIService
from src.services.user_service import UserAIService

logger = get_logger()


class CatalogAIService:
    def __init__(self):
        self.logger = logger
        self.central_ai_service = CentralAIService()
        self.user_ai_service = UserAIService(self.central_ai_service)

    async def enrich_products_batch(
        self,
        payload: EnrichProductsBatchRequest,
        tier: UserTierEnum = UserTierEnum.TIER_2,
    ) -> GenerationResponse:
        """
        Builds the batch classification prompt and invokes UserAIService for LLM parsing.
        """
        try:
            prompt = self._build_enrichment_prompt(payload)
            self.logger.info(f"Routing enrichment prompt for {len(payload.products)} products to UserAIService.")

            response: GenerationResponse = await self.user_ai_service.generate_user_response(
                prompt=prompt,
                tier=tier,
                temperature=0.1,  # Low temperature for deterministic output
            )
            return response

        except HTTPException:
            raise
        except Exception as e:
            self.logger.exception(f"Failure inside CatalogAIService during batch enrichment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to enrich product batch with LLM classification.",
            )

    def _build_enrichment_prompt(self, payload: EnrichProductsBatchRequest) -> str:
        target_schema = json.dumps(EnrichProductsBatchResponse.model_json_schema(), indent=2)
        products_json = json.dumps([p.model_dump() for p in payload.products], indent=2)

        return f"""
System Role: You are an expert e-commerce catalog auditor, financial analyst, and tax classification specialist. 
Your task is to analyze a batch of raw product records, clean metadata, determine valid COICOP/CPC classification codes, and estimate financial baseline hints.

--- INPUT RAW PRODUCTS DATA ---
{products_json}

--- INSTRUCTIONS & RULES ---

1. CANONICAL NAME & BRAND:
   - Extract a clean `canonical_name` from `title`. Remove promotional jargon, pack sizes, and volume specifications (e.g., '120 Ml', '80 Gm').
   - Clean the `brand` name using `manufacturer` or `title` (e.g., 'Dabur India Limited' -> 'Dabur').

2. CLASSIFICATION CODES (COICOP & CPC) & FALLBACK RULE:
   - First, evaluate `candidate_coicop_codes` and `candidate_cpc_codes`.
   - If a candidate accurately describes the product, select its `code` and set `is_coicop_from_candidates` / `is_cpc_from_candidates` to `true`.
   - FALLBACK: If NONE of the provided candidates fit the product, do NOT leave it null. Instead, use your internal knowledge of official COICOP 2018 and UN CPC v2.1 standards to supply the correct standard classification code. Set `is_coicop_from_candidates` / `is_cpc_from_candidates` to `false`.

3. FINANCIAL HINTS & TAX ESTIMATION:
   - `default_currency`: Infer the primary 3-letter ISO currency from brand/regional context (e.g., Indian brands like Dabur -> 'INR', US brands -> 'USD', European -> 'EUR').
   - `typical_price_min` & `typical_price_max`: Provide a realistic local retail price range for the product pack size. If completely impossible to estimate, return null.
   - `default_vat_rate`: Provide the standard statutory VAT / GST percentage rate for this product category in the target region (e.g., 18.0 for 18% GST in India for cosmetics/repellents, 5.0 for basic food items, 20.0 for UK VAT).

4. CUSTOM APP CATEGORY:
   - Provide a clean, user-friendly expense category string (e.g., "Personal Care & Hygiene", "Groceries", "Hardware", "Household Supplies").

5. KEYWORD GENERATION:
   - Generate 4-8 search keywords and classify each with its exact type:
     'PRIMARY', 'BRAND', 'BRAND_VARIANT', 'SYNONYM', 'GENERIC', 'SLANG', 'MISSPELLING'.

6. AUDIT & CONFIDENCE:
   - Assign a `confidence_score` between 0.00 and 1.00 based on data quality and classification accuracy.

--- TARGET JSON SCHEMA ---
Return valid JSON adhering strictly to the following EnrichProductsBatchResponse schema:
{target_schema}
"""