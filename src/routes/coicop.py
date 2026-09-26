import logging
from fastapi import APIRouter, Depends, status

from src.dto.base import SuccessResponse
from src.dto.llm.agent import GenerationResponse
from src.dto.coicop.enrichment import EnrichCOICOPResponse, EnrichCOICOPRequest
from src.services.coicop_service import COICOPService
from src.utils.dto_util import DTOUtils

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/coicop", tags=["COICOP Classification"])


@router.post(
    "/enrich",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[EnrichCOICOPResponse, None],
    summary="Enrich and generate comprehensive metadata profile for a COICOP code"
)
async def enrich_coicop(
        payload: EnrichCOICOPRequest,
        coicop_service: COICOPService = Depends()
) -> SuccessResponse[EnrichCOICOPResponse, None]:
    """
    Accepts a JSON payload with COICOP code and optional context, executes UN COICOP classification parsing,
    and returns icon keywords, description, and vector search concatenations.
    """
    gen_response: GenerationResponse = await coicop_service.enrich_coicop_details(
        coicop_code=payload.coicop_code,
        user_context=payload.user_text,
        tier=payload.tier
    )

    coicop_data = DTOUtils.parse_llm_response(gen_response, EnrichCOICOPResponse)

    return SuccessResponse(
        message="COICOP code enriched successfully",
        data=coicop_data
    )
