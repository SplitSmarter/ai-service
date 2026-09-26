import logging
from typing import Optional
from fastapi import APIRouter, Depends, Form, status

from src.dto.base import SuccessResponse
from src.dto.coicop.enrichment import EnrichCOICOPRequest
from src.dto.enums import UserTierEnum
from src.dto.llm.agent import GenerationResponse
from src.dto.cpc.enrichment import EnrichCPCResponse, EnrichCPCRequest
from src.services.cpc_service import CPCService
from src.utils.dto_util import DTOUtils

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cpc", tags=["Central Product Classification (CPC)"])


@router.post(
    "/enrich",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[EnrichCPCResponse, None],
    summary="Enrich and generate comprehensive metadata profile for a CPC code"
)
async def enrich_cpc(
        payload: EnrichCPCRequest,
        cpc_service: CPCService = Depends()
) -> SuccessResponse[EnrichCPCResponse, None]:
    """
    Accepts a CPC code and optional context, executes UN CPC v2.1 classification parsing,
    and returns brand examples, icon keywords, and vector search concatenations.
    """
    gen_response: GenerationResponse = await cpc_service.enrich_cpc_details(
        cpc_code=payload.cpc_code,
        user_context=payload.user_text,
        tier=payload.tier
    )

    cpc_data = DTOUtils.parse_llm_response(gen_response, EnrichCPCResponse)

    return SuccessResponse(
        message="CPC code enriched successfully",
        data=cpc_data
    )