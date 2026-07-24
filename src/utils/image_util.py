# src/utils/image_utils.py
import logging
from typing import Optional
import httpx
from fastapi import HTTPException, status

from src.dto.ocr import OCRRequest, OCRResponse
from src.services.central_ai_service import CentralAIService

logger = logging.getLogger(__name__)


class ImageUtils:
    def __init__(self, central_ai_service: Optional[CentralAIService] = None):
        """
        Utility class to handle image fetching and passing raw byte streams
        to CentralAIService for OCR/parsing.
        """
        self.central_ai_service = central_ai_service or CentralAIService()

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

    async def extract_text_from_bytes(self, file_bytes: bytes, filename: str = "image.jpg") -> str:
        """
        Routes raw image bytes to CentralAIService OCR pipeline and returns extracted text.
        """
        ocr_response: OCRResponse = await self.central_ai_service.execute_ocr(
            OCRRequest(image_bytes=file_bytes)
        )
        if ocr_response and ocr_response.full_text:
            return ocr_response.full_text
        return ""

    async def parse_image_url(self, image_url: str) -> str:
        """
        Fetches an image from URL and sends its raw bytes to CentralAIService for OCR text extraction.
        """
        logger.info(f"Downloading image from URL: {image_url}")
        image_bytes = await self.fetch_image_bytes(image_url)

        logger.info("Routing downloaded image bytes to CentralAIService OCR pipeline...")
        extracted_text = await self.extract_text_from_bytes(
            file_bytes=image_bytes,
            filename="url_downloaded_image.jpg"
        )

        return extracted_text