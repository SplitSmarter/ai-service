from abc import ABC, abstractmethod
from typing import Union
from src.dto.ocr import OCRResponse
from src.dto.enums import UserTierEnum


class BaseOCRProvider(ABC):
    """Abstract Base Class for all OCR provider strategy implementations."""

    @abstractmethod
    def process_image(self, input_source: Union[str, bytes], tier: UserTierEnum) -> OCRResponse:
        """
        Extracts text and block layout from image source using requested execution tier.

        :param input_source: Local file path string OR raw image bytes.
        :param tier: OCR performance tier.
        :return: Standardized OCRResponse DTO.
        """
        pass