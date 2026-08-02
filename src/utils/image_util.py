# src/utils/image_utils.py
import logging
from typing import Optional
import cv2
import httpx
import numpy as np
from fastapi import HTTPException, status

from src.dto.enums import UserTierEnum
from src.dto.ocr import OCRRequest, OCRResponse
from src.services.central_ai_service import CentralAIService

logger = logging.getLogger(__name__)


class ImageUtils:
    def __init__(self, central_ai_service: Optional[CentralAIService] = None):
        """
        Utility class to handle image fetching, preprocessing, and passing
        byte streams to CentralAIService for OCR/parsing.
        """
        self.central_ai_service = central_ai_service or CentralAIService()

    @staticmethod
    def preprocess_image_bytes(image_bytes: bytes) -> bytes:
        """
        Applies OpenCV preprocessing (grayscale, CLAHE contrast boost, denoising, adaptive thresholding)
        directly on an in-memory byte stream to optimize OCR text extraction accuracy.
        """
        try:
            # TODO: verify this implementation
            # Decode byte array to OpenCV image array
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if img is None:
                logger.warning("OpenCV could not decode image bytes. Skipping preprocessing.")
                return image_bytes

            # Transformation 1: Convert to Grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Transformation 2: Increase Contrast using CLAHE (fixes uneven shadows/lighting)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            contrast_enhanced = clahe.apply(gray)

            # Transformation 3: Denoise to clean up background artifacts
            denoised = cv2.fastNlMeansDenoising(contrast_enhanced, h=10)

            # Transformation 4: Adaptive Thresholding (Binarization to crisp B&W)
            processed = cv2.adaptiveThreshold(
                denoised,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                blockSize=15,
                C=10,
            )

            # Re-encode processed image array back to JPEG byte stream
            is_success, buffer = cv2.imencode(".jpg", processed)
            if not is_success:
                logger.error("Failed to re-encode processed OpenCV image. Using raw image bytes.")
                return image_bytes

            return buffer.tobytes()

        except Exception as e:
            logger.error(f"Error occurred during image preprocessing pipeline: {str(e)}. Returning original bytes.")
            return image_bytes

    async def fetch_image_bytes(self, image_url: str) -> bytes:
        """
        Downloads raw bytes from a remote image URL using an async HTTP client.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(image_url)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "")
                if content_type and not content_type.startswith("image/"):
                    logger.warning(f"URL {image_url} returned non-image content-type: {content_type}")

                return response.content

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error downloading image from {image_url}: {e.response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch image from URL. Remote server returned HTTP {e.response.status_code}."
            )
        except Exception as e:
            logger.error(f"Unexpected error fetching image from {image_url}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve image from provided URL."
            )

    async def extract_text_from_bytes(
            self,
            file_bytes: bytes,
            tier: UserTierEnum,
            preprocess: bool = True
    ) -> str:
        """
        Preprocesses image bytes (optional) and routes them to CentralAIService OCR pipeline.
        """
        target_bytes = file_bytes
        if preprocess:
            logger.info("Applying OpenCV preprocessing transformations to image bytes...")
            target_bytes = self.preprocess_image_bytes(file_bytes)

        ocr_response: OCRResponse = await self.central_ai_service.execute_ocr(
            OCRRequest(image_bytes=target_bytes, tier=tier)
        )
        if ocr_response and ocr_response.full_text:
            return ocr_response.full_text
        return ""

    async def parse_image_url(
            self,
            image_url: str,
            tier: UserTierEnum,
            preprocess: bool = True
    ) -> str:
        """
        Fetches an image from URL, preprocesses it, and sends its raw bytes to CentralAIService for OCR extraction.
        """
        logger.info(f"Downloading image from URL: {image_url}")
        image_bytes = await self.fetch_image_bytes(image_url)

        logger.info("Routing downloaded image bytes through OCR pipeline...")
        extracted_text = await self.extract_text_from_bytes(
            file_bytes=image_bytes,
            tier=tier,
            preprocess=preprocess
        )

        return extracted_text
