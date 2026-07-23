# src/services/user_ai_service.py
import logging
from fastapi import HTTPException, status

from src.config.config import get_logger
from src.dto.agent import GenerationRequest, GenerationResponse
from src.dto.enums import LLMProviderEnum, ExecutionTierEnum
from src.services.central_ai_service import CentralAIService

logger = get_logger()


class UserAIService:
    def __init__(self, central_ai_service: CentralAIService):
        self.logger = logger
        self.central_ai_service = central_ai_service

    async def generate_user_response(
            self,
            prompt: str,
            tier: ExecutionTierEnum,
            temperature: float = 0.7
    ) -> GenerationResponse:
        """
        Accepts simple user parameters, maps them to a structured infrastructure
        GenerationRequest, and processes the text generation cycle.
        """
        try:
            # Determine provider framework. Defaulting to GEMINI as it is the only
            # concrete engine mapped inside CentralAIService's strategy factory map.
            chosen_provider = LLMProviderEnum.GEMINI

            self.logger.info(f"Mapping user request to structural payload. Tier: {tier.value}")

            generation_request = GenerationRequest(
                provider=chosen_provider,
                tier=tier,
                prompt=prompt,
                temperature=temperature
            )

            response: GenerationResponse = await self.central_ai_service.execute_inference(
                request=generation_request
            )

            return response

        except HTTPException:
            # Re-raise operational FastAPI exceptions from downstream dependencies cleanly
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected processing breakdown inside user AI service path: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while routing your text generation request."
            )
