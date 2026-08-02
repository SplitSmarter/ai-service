import logging
from fastapi import APIRouter, Depends, status

from src.dto.base import SuccessResponse
from src.dto.catalog.enrichment import (
    EnrichProductsBatchRequest,
    EnrichProductsBatchResponse,
)
from src.dto.enums import UserTierEnum
from src.dto.llm.agent import GenerationResponse
from src.services.catalog_ai_service import CatalogAIService
from src.utils.dto_util import DTOUtils

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalog", tags=["Catalog AI"])


@router.post(
    "/enrich-batch",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[EnrichProductsBatchResponse, None],
    summary="Classify and enrich raw products with COICOP, CPC, and generated keywords",
)
async def enrich_products_batch(
    payload: EnrichProductsBatchRequest,
    tier: UserTierEnum = UserTierEnum.TIER_2,
    catalog_ai_service: CatalogAIService = Depends(),
) -> SuccessResponse[EnrichProductsBatchResponse, None]:
    """
    Accepts raw product records and potential CPC/COICOP candidate matches, runs LLM-based 
    normalization and classification, and returns structured product enrichment data.
    """
    gen_response: GenerationResponse = await catalog_ai_service.enrich_products_batch(
        payload=payload, tier=tier
    )

    enrichment_data = DTOUtils.parse_llm_response(
        gen_response, EnrichProductsBatchResponse
    )

    return SuccessResponse(
        message="Product batch enriched successfully",
        data=enrichment_data,
    )