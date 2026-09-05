import logging
from fastapi import HTTPException, status

from src.config.config import get_logger
from src.dto.enums import UserTierEnum
from src.dto.llm.agent import GenerationResponse
from src.services.central_ai_service import CentralAIService
from src.services.user_service import UserAIService
from src.dto.chat.query import QueryRequest, QueryResponse

logger = get_logger()


class ChatAIService:
    def __init__(self):
        self.logger = logger
        self.central_ai_service = CentralAIService()
        self.user_ai_service = UserAIService(self.central_ai_service)

    async def execute_query(
            self,
            payload: QueryRequest,
            tier: UserTierEnum = UserTierEnum.TIER_2,
    ) -> QueryResponse:
        """
        Routes a direct query/prompt to UserAIService and returns the LLM output.
        """
        try:
            self.logger.info(f"Routing direct chat query to UserAIService (length: {len(payload.prompt)} chars).")

            response: GenerationResponse = await self.user_ai_service.generate_user_response(
                prompt=payload.prompt,
                tier=tier,
                temperature=payload.temperature,
            )

            # Assuming GenerationResponse has the text output field (adjust based on your actual DTO)
            answer_text = getattr(response, "text", str(response))

            return QueryResponse(answer=answer_text)

        except HTTPException:
            raise
        except Exception as e:
            self.logger.exception(f"Failure inside ChatAIService during query execution: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to execute query with LLM service.",
            )