import google.genai as genai
from google.genai import types

from src.config.config import MAX_OUTPUT_TOKENS
from src.services.llm.base import BaseLLMProvider
from src.dto.agent import GenerationRequest, GenerationResponse, GenerationResponseMetadata
from src.dto.gemini_schema import GeminiUsageMetadata


class GeminiProvider(BaseLLMProvider):

    async def generate_text(self, request: GenerationRequest, api_key: str, resolved_model: str) -> GenerationResponse:
        client = genai.Client(api_key=api_key)

        config = types.GenerateContentConfig(
            temperature=request.temperature,
            max_output_tokens=MAX_OUTPUT_TOKENS
        )

        raw_sdk_output = await client.aio.models.generate_content(
            model=resolved_model,
            contents=request.prompt,
            config=config
        )

        extracted_text = raw_sdk_output.text or ""
        total_tokens = 0
        parsed_usage = None

        if raw_sdk_output.usage_metadata:
            total_tokens = raw_sdk_output.usage_metadata.total_token_count or 0
            parsed_usage = GeminiUsageMetadata.model_validate(
                raw_sdk_output.usage_metadata,
                from_attributes=True
            )

        return GenerationResponse(
            text=extracted_text,
            tokens_used=total_tokens,
            meta=GenerationResponseMetadata(
                model_processed=resolved_model,
                key_identifier_used="",
                raw_usage=parsed_usage
            )
        )