# src/services/expense_service.py
import json
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, UploadFile, status

from src.config.config import get_logger
from src.dto.agent import GenerationResponse
from src.dto.enums import ExecutionTierEnum
from src.dto.expense.expense import ExtractedExpenseDraftResponse
from src.dto.ocr import OCRRequest, OCRResponse
from src.services.central_ai_service import CentralAIService
from src.services.user_service import UserAIService
from src.utils.image_util import ImageUtils

logger = get_logger()


class ExpenseService:
    def __init__(self):
        self.logger = logger
        self.central_ai_service = CentralAIService()
        self.user_ai_service = UserAIService(self.central_ai_service)
        self.image_utils = ImageUtils(self.central_ai_service)

    async def extract_expense_from_receipt(
        self,
        files: List[UploadFile],
        user_text: Optional[str],
        current_user_name: str,
        tier: ExecutionTierEnum = ExecutionTierEnum.TIER_4
    ) -> GenerationResponse:
        """
        Extracts OCR via CentralAIService, merges user notes, crafts the structured
        prompt, and delegates generation to UserAIService.
        """
        try:
            # 1. Extract raw text from files using CentralAIService OCR
            raw_ocr_texts = []
            for file in files:
                file_bytes = await file.read()
                ocr_response: OCRResponse = await self.central_ai_service.execute_ocr(
                    OCRRequest(image_bytes=file_bytes)
                )
                if ocr_response and ocr_response.full_text:
                    raw_ocr_texts.append(ocr_response.full_text)

            combined_ocr_text = (
                "\n--- NEXT FILE ---\n".join(raw_ocr_texts)
                if raw_ocr_texts else "NO_OCR_TEXT_FOUND"
            )

            # 2. Build structured extraction prompt
            extraction_prompt = self._build_extraction_prompt(
                ocr_text=combined_ocr_text,
                user_text=user_text,
                current_user_name=current_user_name
            )

            self.logger.info("Routing prompt to UserAIService for structured inference.")

            # 3. Delegate prompt execution to UserAIService with low temperature (0.1)
            response: GenerationResponse = await self.user_ai_service.generate_user_response(
                prompt=extraction_prompt,
                tier=tier,
                temperature=0.1
            )

            return response

        except HTTPException:
            raise
        except Exception as e:
            self.logger.exception(f"Failure inside ExpenseService during receipt processing: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process and extract expense details from provided receipt inputs."
            )

    async def extract_expense_from_urls(
        self,
        image_urls: List[str],
        user_text: Optional[str],
        current_user_name: str,
        tier: ExecutionTierEnum = ExecutionTierEnum.TIER_4
    ) -> GenerationResponse:
        """
        Downloads receipt images from remote URLs, extracts text via ImageUtils,
        and delegates structured expense extraction to UserAIService.
        """
        try:
            raw_ocr_texts = []

            for url in image_urls:
                self.logger.info(f"Downloading and processing image from URL: {url}")
                # Downloads image bytes and runs OCR extraction
                extracted_text = await self.image_utils.parse_image_url(image_url=url)
                if extracted_text and extracted_text.strip():
                    raw_ocr_texts.append(extracted_text)

            combined_ocr_text = (
                "\n--- NEXT FILE ---\n".join(raw_ocr_texts)
                if raw_ocr_texts else "NO_OCR_TEXT_FOUND"
            )

            extraction_prompt = self._build_extraction_prompt(
                ocr_text=combined_ocr_text,
                user_text=user_text,
                current_user_name=current_user_name
            )

            self.logger.info("Routing prompt from URL extraction to UserAIService.")

            response: GenerationResponse = await self.user_ai_service.generate_user_response(
                prompt=extraction_prompt,
                tier=tier,
                temperature=0.1
            )

            return response

        except HTTPException:
            raise
        except Exception as e:
            self.logger.exception(f"Failure inside ExpenseService during URL processing: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process and extract expense details from provided image URLs."
            )

    def _build_extraction_prompt(
        self,
        ocr_text: str,
        user_text: Optional[str],
        current_user_name: str
    ) -> str:
        """
        Constructs a structured prompt instructing the LLM on COICOP/CPC classification,
        date rules, place extraction, and math delegation.
        """
        today_str = datetime.now().strftime("%Y-%m-%d (%A)")
        target_schema = json.dumps(ExtractedExpenseDraftResponse.model_json_schema(), indent=2)

        return f"""
System Role: You are an expert financial expense parser. Extract receipt and user note details into structured data according to these rules:

--- INPUT DATA ---
Today's Reference Date: {today_str}
Logged-in User Name: {current_user_name}

[RAW OCR TEXT FROM RECEIPT]
{ocr_text}

[USER CONTEXT / OVERRIDE NOTES]
{user_text or 'None provided'}

--- EXTRACTION RULES ---
1. CONFLICT RESOLUTION: User context overrides OCR if they explicitly contradict each other.
2. CATEGORY CLASSIFICATION: Use standard COICOP (Classification of Individual Consumption According to Purpose) code and name.
3. LINE ITEMS & CPC: For each item, extract raw text and assign a CPC (Central Product Classification) subclass keyword.
4. ZERO MATH EXECUTION: Do NOT perform math. Extract raw printed 'quantity', 'unit_cost', and explicit totals as printed on the receipt.
5. PLACE DETAILS: Extract optional city, state, country, and store name if present. Return null if no location details exist.
6. GROUPS: Extract group_name if explicitly mentioned in user notes.
7. DATES:
   - Fixed expense: set `is_recurring` = false, provide `expense_date` (YYYY-MM-DD), and set `recurring_details` = null.
   - Recurring expense: set `is_recurring` = true, set `expense_date` = null, and populate `recurring_details`.
8. PAYER & SHARERS: Default paid_by and sharers to '{current_user_name}' if no other names are provided. Set shared_towards to "TOTAL".

--- TARGET JSON SCHEMA ---
Return valid JSON adhering strictly to the following ExtractedExpenseDraftResponse schema:
{target_schema}
"""