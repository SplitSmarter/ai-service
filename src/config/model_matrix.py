from src.dto.enums import LLMProviderEnum, ExecutionTierEnum, GeminiModelEnum, OpenAIModelEnum

# Matrix mapping [Provider][Tier] -> Specific Model String
PROVIDER_TIER_MODEL_MATRIX: dict[LLMProviderEnum, dict[ExecutionTierEnum, str]] = {
    LLMProviderEnum.GEMINI: {
        ExecutionTierEnum.TIER_1: GeminiModelEnum.FLASH_2_5.value,
        ExecutionTierEnum.TIER_2: GeminiModelEnum.FLASH_2_5.value,  # Fallbacks or specific versions can match
        ExecutionTierEnum.TIER_3: GeminiModelEnum.PRO_2_5.value,
        ExecutionTierEnum.TIER_4: GeminiModelEnum.FLASH_THINKING.value,
    },
    LLMProviderEnum.OPENAI: {
        ExecutionTierEnum.TIER_1: OpenAIModelEnum.GPT_4O_MINI.value,
        ExecutionTierEnum.TIER_2: OpenAIModelEnum.GPT_4O.value,
        ExecutionTierEnum.TIER_3: OpenAIModelEnum.O1_MINI.value,
        ExecutionTierEnum.TIER_4: OpenAIModelEnum.O3_MINI.value,
    }
}


def resolve_model_name(provider: LLMProviderEnum, tier: ExecutionTierEnum) -> str:
    """Helper resolution utility to pull the model mapping from the matrix securely."""
    provider_matrix = PROVIDER_TIER_MODEL_MATRIX.get(provider)
    if not provider_matrix:
        raise ValueError(f"Unregistered infrastructure provider framework: {provider}")

    model_name = provider_matrix.get(tier)
    if not model_name:
        raise ValueError(f"Execution Tier {tier} is currently unmapped for provider platform: {provider}")

    return model_name