# src/services/central_ai_service.py
import logging
from typing import Union
from fastapi import HTTPException, status

from src.dto.agent import GenerationRequest, GenerationResponse
from src.dto.ocr import OCRRequest, OCRResponse
from src.dto.enums import LLMProviderEnum
from src.config.model_matrix import resolve_model_name

from src.services.manager.key_manager import DynamicRotationManager
from src.services.llm.base import BaseLLMProvider
from src.services.llm.gemini import GeminiProvider
from src.services.ocr.vision_provider import GoogleVisionOCRProvider


class CentralAIService:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        # Strategy Factory Map for LLMs
        self._provider_factory: dict[LLMProviderEnum, BaseLLMProvider] = {
            LLMProviderEnum.GEMINI: GeminiProvider()
        }
        # OCR Engine Instance
        self._ocr_provider = GoogleVisionOCRProvider(logger=self.logger)

    async def execute_ocr(self, request: OCRRequest) -> OCRResponse:
        """Processes images via OCR to extract text and block layouts."""
        try:
            input_source = request.image_bytes or request.image_path
            if not input_source:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either 'image_path' or 'image_bytes' must be provided."
                )

            self.logger.info("Starting Google Vision OCR text extraction pipeline...")
            ocr_result = self._ocr_provider.process_image(input_source)
            self.logger.info(f"OCR completed successfully. Extracted {len(ocr_result.blocks)} blocks.")

            return ocr_result

        except FileNotFoundError as fnf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(fnf))
        except HTTPException:
            raise
        except Exception as e:
            self.logger.exception(f"Unhandled failure during OCR execution: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OCR processing failed inside central AI service core."
            )

    async def execute_inference(self, request: GenerationRequest) -> GenerationResponse:
        """Orchestrates full operational lifecycle pipelines behind a single interface call."""
        engine = self._provider_factory.get(request.provider)
        if not engine:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported model provider infrastructure selection: '{request.provider}'"
            )

        try:
            target_model_string = resolve_model_name(request.provider, request.tier)

            rotator = DynamicRotationManager(self.logger)
            key_identifier, valid_api_key = await rotator.select_least_used_key(request.provider.value)

            response: GenerationResponse = await engine.generate_text(
                request=request,
                api_key=valid_api_key,
                resolved_model=target_model_string
            )

            await rotator.commit_usage_metrics(request.provider.value, key_identifier, response.tokens_used)
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