# src/services/ocr/google_vision.py
import io
import os
import logging
from typing import Union, Optional
from google.cloud import vision

from src.dto.ocr import OCRResponse
from src.dto.enums import UserTierEnum
from src.services.ocr.base import BaseOCRProvider


class GoogleVisionOCRProvider(BaseOCRProvider):
    """Service wrapper for Google Cloud Vision Document Text Detection."""

    def __init__(self, credentials_path: Optional[str] = None, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

        self.client = vision.ImageAnnotatorClient()

    def process_image(self, input_source: Union[str, bytes], tier: UserTierEnum = UserTierEnum.TIER_3) -> OCRResponse:
        """Processes image via Google Cloud Vision API."""
        try:
            if isinstance(input_source, bytes):
                content = input_source
            elif isinstance(input_source, str):
                if not os.path.exists(input_source):
                    raise FileNotFoundError(f"Target image path does not exist: {input_source}")
                with io.open(input_source, 'rb') as image_file:
                    content = image_file.read()
            else:
                raise ValueError("Invalid input source. Expected image path string or raw bytes.")

            image = vision.Image(content=content)
            response = self.client.document_text_detection(image=image)

            if response.error.message:
                self.logger.error(f"Google Vision API Error: {response.error.message}")
                raise Exception(f"Google Vision API Error: {response.error.message}")

            annotation = response.full_text_annotation
            full_text = annotation.text if annotation else ""

            blocks_text: list[str] = []
            if annotation and annotation.pages:
                for page in annotation.pages:
                    for block in page.blocks:
                        block_words = []
                        for paragraph in block.paragraphs:
                            for word in paragraph.words:
                                word_text = ''.join([symbol.text for symbol in word.symbols])
                                block_words.append(word_text)

                        block_str = ' '.join(block_words).strip()
                        if block_str:
                            blocks_text.append(block_str)

            total_pages = len(annotation.pages) if annotation and annotation.pages else 0

            return OCRResponse(
                full_text=full_text,
                blocks=blocks_text,
                total_pages=total_pages
            )

        except Exception as e:
            self.logger.exception(f"Failed to execute Vision OCR processing: {str(e)}")
            raise