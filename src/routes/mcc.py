import logging
from fastapi import APIRouter, Depends, status

from src.dto.base import SuccessResponse
from src.dto.llm.agent import GenerationResponse
from src.dto.mcc.enrichment import EnrichMCCResponse, EnrichMCCRequest
from src.services.mcc_service import MCCService
from src.utils.dto_util import DTOUtils

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcc", tags=["Merchant Category Codes"])


@router.post(
    "/enrich",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[EnrichMCCResponse, None],
    summary="Enrich and generate complete metadata profile for a Merchant Category Code (MCC)"
)
async def enrich_mcc(
        payload: EnrichMCCRequest,
        mcc_service: MCCService = Depends()
) -> SuccessResponse[EnrichMCCResponse, None]:
    """
    Accepts an MCC code and optional user context, executes LLM classification matching
    ISO 18245 standards, and returns database-ready record attributes.
    """
    gen_response: GenerationResponse = await mcc_service.enrich_mcc_details(
        mcc_code=payload.mcc_code,
        user_context=payload.user_text,
        tier=payload.tier
    )

    mcc_data = DTOUtils.parse_llm_response(gen_response, EnrichMCCResponse)

    return SuccessResponse(
        message="MCC code enriched successfully",
        data=mcc_data
    )
