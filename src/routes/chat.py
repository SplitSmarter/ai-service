import logging
from fastapi import APIRouter, Depends, status

from src.dto.base import SuccessResponse
from src.dto.chat.query import QueryRequest, QueryResponse
from src.dto.enums import UserTierEnum
from src.services.chat_ai_service import ChatAIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["Chat AI"])


@router.post(
    "/query",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[QueryResponse, None],
    summary="Directly interact with the LLM via a prompt query",
)
async def query_ai_service(
        payload: QueryRequest,
        tier: UserTierEnum = UserTierEnum.TIER_3,
        chat_ai_service: ChatAIService = Depends(),
) -> SuccessResponse[QueryResponse, None]:
    """
    Accepts a raw text prompt, runs it through the central/user AI service,
    and returns the generated response directly.
    """
    query_response = await chat_ai_service.execute_query(payload=payload, tier=tier)

    return SuccessResponse(
        message="Query executed successfully",
        data=query_response,
    )
