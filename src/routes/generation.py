import logging
from fastapi import APIRouter, HTTPException, status, Depends
from src.config.config import get_request_logger
from src.config.model_matrix import resolve_model_name  # ◄── Imported resolution map helper
from src.dto.enums import LLMProviderEnum
from src.dto.agent import GenerationRequest, GenerationResponse

from src.services.manager.key_manager import DynamicRotationManager
from src.services.llm.gemini import GeminiProvider

# from src.services.llm.openai import OpenAIProvider (Example reference)

logger = logging.getLogger("ai_service.generation")
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
        # 1. Dynamically resolve specific vendor string target using provider + incoming execution tier code
        target_model_string = resolve_model_name(payload.provider, payload.tier)

        # 2. Select the least-used rotated key matching config tracking signatures
        rotator = DynamicRotationManager(logger)
        key_identifier, valid_api_key = await rotator.select_least_used_key(payload.provider.value)

        # 3. Fire call directly with the target vendor model context resolved
        response: GenerationResponse = await engine.generate_text(payload, valid_api_key, target_model_string)

        # 4. Save metadata metrics out to core Redis channels
        await rotator.commit_usage_metrics(payload.provider.value, key_identifier, response.tokens_used)

        response.meta.key_identifier_used = key_identifier
        return response

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Critical error mapping execution matrix request processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Central Core Gateway processing failure encountered during target tier generation loop."
        )