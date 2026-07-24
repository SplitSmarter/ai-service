from src.dto.enums import OCRProviderEnum, UserTierEnum

# Matrix mapping [Provider][Tier] -> Specific Model String
PROVIDER_TIER_MODEL_MATRIX: dict[UserTierEnum, OCRProviderEnum] = {
    UserTierEnum.TIER_1: OCRProviderEnum.EASY_OCR.value,
    UserTierEnum.TIER_2: OCRProviderEnum.GOOGLE_VISION.value,  # Fallbacks or specific versions can match
    UserTierEnum.TIER_3: OCRProviderEnum.GOOGLE_VISION.value,
    UserTierEnum.TIER_4: OCRProviderEnum.GOOGLE_VISION.value,
}


def resolve_provider_name(tier: UserTierEnum) -> OCRProviderEnum:
    """Helper resolution utility to pull the model mapping from the matrix securely."""
    model_name = PROVIDER_TIER_MODEL_MATRIX.get(tier)
    if not model_name:
        raise ValueError(f"Execution Tier {tier} is currently unmapped")

    return model_name
