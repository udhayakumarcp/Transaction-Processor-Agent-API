"""Types for the app"""

from enum import Enum


class AiModel(str, Enum):
    """Enum class for AiModel"""

    GEMINI = "Gemini"
    DEEP_SEEK = "DeepSeek"
