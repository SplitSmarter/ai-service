from abc import ABC, abstractmethod
from src.dto.agent import GenerationRequest, GenerationResponse

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_text(self, request: GenerationRequest, api_key: str, resolved_model: str) -> GenerationResponse:
        """Executes text inference against a specific vendor API endpoint."""
        pass