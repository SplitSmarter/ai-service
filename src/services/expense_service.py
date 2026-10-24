# src/services/expense_service.py
import json
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, UploadFile, status

from src.config.config import get_logger
from src.dto.llm.agent import GenerationResponse
from src.dto.enums import UserTierEnum
from src.dto.expense.expense import ExtractedExpenseDraftResponse
from src.dto.ocr import OCRRequest, OCRResponse
from src.services.central_ai_service import CentralAIService
from src.services.user_service import UserAIService
from src.utils.dto_util import DTOUtils
from src.utils.image_util import ImageUtils

logger = get_logger()

# Extra LLM calls after a draft fails schema validation. OCR is not repeated.
LLM_PARSE_RETRIES = 1


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
        tier: UserTierEnum = UserTierEnum.TIER_4
    ) -> ExtractedExpenseDraftResponse:
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
                    OCRRequest(image_bytes=file_bytes, tier=tier)
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
            return await self._generate_valid_draft(extraction_prompt, tier)

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
        tier: UserTierEnum = UserTierEnum.TIER_2
    ) -> ExtractedExpenseDraftResponse:
        """
        Downloads receipt images from remote URLs, extracts text via ImageUtils,
        and delegates structured expense extraction to UserAIService.
        """
        try:
            raw_ocr_texts = []

            for url in image_urls:
                self.logger.info(f"Downloading and processing image from URL: {url}")
                # Downloads image bytes and runs OCR extraction
                extracted_text = await self.image_utils.parse_image_url(image_url=url, tier=tier)
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
            return await self._generate_valid_draft(extraction_prompt, tier)

        except HTTPException:
            raise
        except Exception as e:
            self.logger.exception(f"Failure inside ExpenseService during URL processing: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process and extract expense details from provided image URLs."
            )

    async def _generate_valid_draft(
            self,
            prompt: str,
            tier: UserTierEnum,
    ) -> ExtractedExpenseDraftResponse:
        active_prompt = prompt
        for attempt in range(LLM_PARSE_RETRIES + 1):
            response: GenerationResponse = await self.user_ai_service.generate_user_response(
                prompt=active_prompt,
                tier=tier,
                temperature=0.1,
            )
            try:
                return DTOUtils.parse_llm_response(response, ExtractedExpenseDraftResponse)
            except HTTPException as exc:
                if attempt >= LLM_PARSE_RETRIES:
                    raise
                self.logger.warning(
                    "Receipt extract failed validation, retrying once: %s", exc.detail
                )
                active_prompt = (
                    f"{prompt}\n\n--- CORRECTION ---\n"
                    "The previous JSON failed validation:\n"
                    f"{exc.detail}\n"
                    "Return only valid JSON for ExtractedExpenseDraftResponse. "
                )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to validate LLM output into ExtractedExpenseDraftResponse",
        )

    def _build_extraction_prompt(
        self,
        ocr_text: str,
        user_text: Optional[str],
        current_user_name: str
    ) -> str:
        """
        Receipt fact extractor prompt: shared facts for expense and transfer drafting.
        No domain classification, no DB IDs, no arithmetic.
        """
        today_str = datetime.now().strftime("%Y-%m-%d (%A)")
        target_schema = json.dumps(ExtractedExpenseDraftResponse.model_json_schema(), indent=2)

        return f"""
System: You extract structured RECEIPT FACTS for downstream expense and transfer drafting.
You do NOT classify domain (expense vs transfer). You do NOT return database IDs. You do NOT do arithmetic.

--- INPUT DATA ---
Today's Reference Date: {today_str}

[USER CONTEXT / OVERRIDE NOTES]
{user_text or 'None provided'}

[RAW OCR TEXT FROM RECEIPT]
{ocr_text}

--- GLOBAL RULES ---
1. CONFLICT: user_text overrides OCR when they explicitly contradict.
2. ZERO MATH: never sum tax lines, never invent grand total, never divide line totals into unit prices.
3. NO ACCOUNT PII: payment_method_hint is rail only (upi/card/cash/wallet/bank or short printed word). Never return card last-4, UPI ids, or account numbers.
4. NO DOMAIN LABEL: do not output domain/expense/transfer create objects.
5. DEFAULT is_recurring=false and recurring_details=null unless user_text explicitly requests recurring.

--- FIELD GUIDANCE ---
- printed_grand_total (REQUIRED): labeled TOTAL / GRAND TOTAL / AMOUNT DUE / NET PAYABLE. Prefer amount due over subtotal.
- currency: ISO-4217 when detectable; else null.
- date_details: Output the date strictly in ISO 8601 format: YYYY-MM-DD; else null. is_recurring=false for receipts.
- merchant: optional object with name + merchant_alias (other names, preference ordered) when a store/brand appears; omit if unknown. Also set merchant_name for compatibility.
- payment_method_hint: from footer (UPI, VISA, CASH, …) — rail type only.
- place_details: address block; include match_keywords and preference-ordered search_queries when possible.
- coicop_category: overall purchase purpose with optional confidence; always fill category_name_candidates (ordered fallbacks).
- items[]: MERCHANDISE ONLY. Skip SUBTOTAL, TAX, TOTAL, CHANGE, GSTIN, card masks. Fill item_name_candidates (specific→generic), match_keywords, cpc/coicop hints when confident.
  QUANTITY: If quantity is printed on the line (Qty, x2, 2 x, @, etc.), set `quantity` to that exact integer. If quantity is NOT printed, set `quantity` to 1 — never invent a qty from totals.
  PRICE: Prefer printed unit_cost when a unit price is shown. If only a line total is printed, set `explicit_line_total` to that amount, leave `unit_cost` null, and keep `quantity` as above (usually 1). Do not divide line total by qty to invent unit_cost.
- adjustments[]: ONE entry per printed NON-MERCHANDISE money row. kind enum TAX|TIP|FEE|DISCOUNT|ROUNDING|OTHER. amount = absolute printed magnitude and MUST be greater than 0. Omit a row whose printed amount is 0. raw_label = printed label. CGST and SGST = two TAX rows — never merge. Never put tax/tip/fee/discount/total into items[].
- paid_by / sharers: leave EMPTY arrays unless names appear in OCR or user notes. Name the logged-in user exactly "self". Never replace "self" with the logged-in display name. Copy every other person's name as written. Set amount only when that person's amount is explicitly stated. Never calculate a remainder or split the total yourself.
- group_name / counterparty_user_name: only if explicitly present in notes/OCR.
- description: optional short summary without digits; else null.
- title: optional short title distinct from merchant; else null.

--- TARGET JSON SCHEMA ---
Return valid JSON only, adhering strictly to ExtractedExpenseDraftResponse:
{target_schema}
"""