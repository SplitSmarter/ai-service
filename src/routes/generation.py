import logging
from fastapi import APIRouter, HTTPException, status, Depends
from src.config.config import get_request_logger
from src.config.model_matrix import resolve_model_name  # ◄── Imported resolution map helper
from src.dto.enums import LLMProviderEnum
from src.dto.agent import GenerationRequest, GenerationResponse
from src.services.central_ai_service import CentralAIService

from src.services.manager.key_manager import DynamicRotationManager
from src.services.llm.gemini import GeminiProvider

# from src.services.llm.openai import OpenAIProvider (Example reference)

router = APIRouter(prefix="/v1/ai", tags=["Central Core AI Gateway"])

# Stateless factory strategy map instances
PROVIDER_FACTORY_MAP = {
    LLMProviderEnum.GEMINI: GeminiProvider()
    # LLMProviderEnum.OPENAI: OpenAIProvider()
}


@router.post("/generate", response_model=GenerationResponse)
async def process_balanced_inference(
        payload: GenerationRequest,
        logger=Depends(get_request_logger)
):
    engine = PROVIDER_FACTORY_MAP.get(payload.provider)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported model provider framework infrastructure selection: '{payload.provider}'"
        )

    try:
        ai_service = CentralAIService(logger)
        return await ai_service.execute_inference(payload)

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Critical error mapping execution matrix request processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Central Core Gateway processing failure encountered during target tier generation loop."
        )
