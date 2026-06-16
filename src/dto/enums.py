from enum import Enum, IntEnum


class LLMProviderEnum(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"


class ExecutionTierEnum(IntEnum):
    """
    1 = Lightweight/Fastest (Flash / Mini models)
    2 = Balanced standard capability
    3 = Advanced/Large-context reasoning
    4 = Elite/Heavy Reasoning (Ultra / Thinker models)
    """
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3
    TIER_4 = 4


class GeminiModelEnum(str, Enum):
    FLASH_2_5 = "gemini-2.5-flash"
    PRO_2_5 = "gemini-2.5-pro"
    # Keeping it flexible to support experimental/thinking models if needed later
    FLASH_THINKING = "gemini-2.5-flash-thinking-exp"


class OpenAIModelEnum(str, Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"
    O1_MINI = "o1-mini"
    O3_MINI = "o3-mini"


class MediaModalityEnum(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"


class FinishReasonEnum(str, Enum):
    STOP = "STOP"
    MAX_TOKENS = "MAX_TOKENS"
    SAFETY = "SAFETY"
    RECITATION = "RECITATION"
    OTHER = "OTHER"
