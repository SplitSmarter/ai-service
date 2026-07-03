# from openai import AsyncOpenAI
from src.config.config import MAX_OUTPUT_TOKENS
from src.services.llm.base import BaseLLMProvider
from src.dto.agent import GenerationRequest, GenerationResponse


class OpenAIProvider(BaseLLMProvider):

    async def generate_text(self, request: GenerationRequest, api_key: str, resolved_model: str) -> GenerationResponse:
        # Client initialized dynamically per call using the selected rotated token
        # client = AsyncOpenAI(api_key=api_key)
        client = None

        response = await client.chat.completions.create(
            model=resolved_model,
            messages=[{"role": "user", "content": request.prompt}],
            temperature=request.temperature,
            max_tokens=MAX_OUTPUT_TOKENS
        )

        total_tokens = response.usage.total_tokens if response.usage else 0

        return GenerationResponse(
            text=response.choices[0].message.content or "",
            tokens_used=total_tokens,
            meta={"model_processed": self.model_name}
        )