# src/services/ai_service.py
import logging
from fastapi import HTTPException, status
from src.dto.agent import GenerationRequest, GenerationResponse
from src.dto.enums import LLMProviderEnum
from src.config.model_matrix import resolve_model_name

# Strategy, Strategy Factory Map & Management Layers
from src.services.manager.key_manager import DynamicRotationManager
from src.services.llm.base import BaseLLMProvider
from src.services.llm.gemini import GeminiProvider


# from src.services.llm.openai import OpenAIProvider (Add here when expanding)

class CentralAIService:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        # Centralized Factory Mapping Registry
        self._provider_factory: dict[LLMProviderEnum, BaseLLMProvider] = {
            LLMProviderEnum.GEMINI: GeminiProvider()
            # LLMProviderEnum.OPENAI: OpenAIProvider()
        }

    async def execute_inference(self, request: GenerationRequest) -> GenerationResponse:
        """
        Orchestrates full operational lifecycle pipelines behind a single interface call.
        Handles resolving models, rotating keys, invoking vendor SDKs, and syncing metrics.
        """
        # 1. Fetch appropriate implementation strategy from the factory mapping
        engine = self._provider_factory.get(request.provider)
        if not engine:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported model provider infrastructure selection: '{request.provider}'"
            )

        try:
            # 2. Resolve the infrastructure specific model string via provider + tier matrix
            target_model_string = resolve_model_name(request.provider, request.tier)

            # 3. Handle Least-Used key balancing strategies dynamically
            rotator = DynamicRotationManager(self.logger)
            key_identifier, valid_api_key = await rotator.select_least_used_key(request.provider.value)

            # 4. Fire target call down to corresponding asynchronous provider pipeline
            response: GenerationResponse = await engine.generate_text(
                request=request,
                api_key=valid_api_key,
                resolved_model=target_model_string
            )

            # 5. Commit token counts out to ContextVars and Redis storage registers automatically
            await rotator.commit_usage_metrics(request.provider.value, key_identifier, response.tokens_used)

            # Enrich response object metadata with runtime traces
            response.meta.key_identifier_used = key_identifier
            return response

        except ValueError as ve:
            self.logger.warning(f"Validation constraints triggered during key configuration lookups: {str(ve)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        except HTTPException:
            raise
        except Exception as e:
            self.logger.exception(f"Unhandled operational crash captured inside central inference thread: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Central Core Gateway processing failure encountered during target tier generation loop."
            )