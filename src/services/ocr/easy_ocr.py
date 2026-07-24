# src/services/ocr/easyocr_provider.py
import os
import tempfile
import logging
from typing import Union, Optional
import easyocr

from src.dto.ocr import OCRResponse
from src.dto.enums import UserTierEnum
from src.services.ocr.base import BaseOCRProvider


class EasyOCRProvider(BaseOCRProvider):
    """Strategy provider implementation for EasyOCR engine."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        # Lazy initialization of readers to save startup memory
        self._cpu_reader: Optional[easyocr.Reader] = None
        self._gpu_reader: Optional[easyocr.Reader] = None

    def _get_reader(self, use_gpu: bool) -> easyocr.Reader:
        """Instantiates EasyOCR reader lazily on demand."""
        if use_gpu:
            if not self._gpu_reader:
                self.logger.info("Initializing EasyOCR Reader (GPU enabled)...")
                self._gpu_reader = easyocr.Reader(['en'], gpu=True)
            return self._gpu_reader
        else:
            if not self._cpu_reader:
                self.logger.info("Initializing EasyOCR Reader (CPU mode)...")
                self._cpu_reader = easyocr.Reader(['en'], gpu=False)
            return self._cpu_reader

    def process_image(self, input_source: Union[str, bytes], tier: UserTierEnum) -> OCRResponse:
        """Processes image using EasyOCR based on requested performance tier."""
        temp_file_path: Optional[str] = None
        try:
            # Handle Tier configuration: Tier 1 -> CPU, Tier 2+ -> GPU
            use_gpu = tier != UserTierEnum.TIER_1
            reader = self._get_reader(use_gpu=use_gpu)

            # EasyOCR expects a file path or numpy array. Write bytes to temporary file if necessary.
            if isinstance(input_source, bytes):
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                temp_file.write(input_source)
                temp_file.close()
                target_path = temp_file.name
                temp_file_path = target_path
            elif isinstance(input_source, str):
                if not os.path.exists(input_source):
                    raise FileNotFoundError(f"Target image path does not exist: {input_source}")
                target_path = input_source
            else:
                raise ValueError("Invalid input source. Expected image path string or raw bytes.")

            # Perform OCR text detection
            results = reader.readtext(target_path, detail=1)

            if not results:
                return OCRResponse(full_text="", blocks=[], total_pages=1)

            # Build full text and block list
            blocks: list[str] = []
            full_text_lines: list[str] = []

            for item in results:
                text = item[1].strip()
                if text:
                    blocks.append(text)
                    full_text_lines.append(text)

            full_text = " ".join(full_text_lines)

            return OCRResponse(
                full_text=full_text,
                blocks=blocks,
                total_pages=1
            )

        except Exception as e:
            self.logger.exception(f"Failed to execute EasyOCR processing: {str(e)}")
            raise
        finally:
            # Clean up temporary file if created
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as cleanup_err:
                    self.logger.warning(f"Failed to delete temp OCR file {temp_file_path}: {cleanup_err}")