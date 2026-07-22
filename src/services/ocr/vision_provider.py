# src/services/ocr/vision_provider.py
import io
import os
import logging
from typing import Union, Optional
from google.cloud import vision

from src.dto.ocr import OCRResponse


class GoogleVisionOCRProvider:
    """Service wrapper for Google Cloud Vision Document Text Detection."""

    def __init__(self, credentials_path: Optional[str] = None, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

        # Fallback to standard environment setting if path provided
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

        # Initialize Google Vision Client
        self.client = vision.ImageAnnotatorClient()

    def process_image(self, input_source: Union[str, bytes]) -> OCRResponse:
        """
        Processes image via Google Cloud Vision API.

        :param input_source: File path string OR raw image byte stream.
        :return: Structured OCRResponse object.
        """
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

            # Perform document text detection (optimized for dense documents/bills/receipts)
            response = self.client.document_text_detection(image=image)

            if response.error.message:
                self.logger.error(f"Google Vision API Error: {response.error.message}")
                raise Exception(f"Google Vision API Error: {response.error.message}")

            annotation = response.full_text_annotation
            full_text = annotation.text if annotation else ""

            # Parse block-level layout structure
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