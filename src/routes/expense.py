# src/routes/expense.py
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from pydantic import BaseModel, Field

from src.dto.agent import GenerationResponse
from src.dto.enums import ExecutionTierEnum
from src.dto.expense.expense import ExtractedExpenseDraftResponse
from src.services.expense_service import ExpenseService
from src.utils.dto_util import DTOUtils

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post(
    "/extract",
    status_code=status.HTTP_200_OK,
    response_model=ExtractedExpenseDraftResponse,
    summary="Extract draft expense details from receipt files and user prompt"
)
async def extract_expense(
    files: List[UploadFile] = File([], description="Uploaded receipt image or PDF files"),
    user_text: Optional[str] = Form(None, description="Optional notes or contextual text from user"),
    current_user_name: str = Form("Default User", description="Logged in user name context"),
    tier: ExecutionTierEnum = Form(ExecutionTierEnum.TIER_1),
    expense_service: ExpenseService = Depends()
) -> ExtractedExpenseDraftResponse:
    """
    Accepts raw receipt files along with optional user context strings, extracts OCR,
    and returns structured draft expense details.
    """
    gen_response: GenerationResponse = await expense_service.extract_expense_from_receipt(
        files=files,
        user_text=user_text,
        current_user_name=current_user_name,
        tier=tier
    )

    return DTOUtils.parse_llm_response(gen_response, ExtractedExpenseDraftResponse)


# DTO for the URL Extraction Test Endpoint
class ExtractFromUrlsRequest(BaseModel):
    image_urls: List[str] = Field(..., description="List of remote image URLs to process")
    user_text: Optional[str] = Field(None, description="Optional notes or contextual text from user")
    current_user_name: str = Field("Default User", description="Logged-in user name")
    tier: ExecutionTierEnum = Field(ExecutionTierEnum.TIER_4, description="Execution tier")


@router.post(
    "/extract-from-urls",
    status_code=status.HTTP_200_OK,
    response_model=ExtractedExpenseDraftResponse,
    summary="Test endpoint: Extract expense details from a list of remote image URLs"
)
async def extract_expense_from_urls(
    payload: ExtractFromUrlsRequest,
    expense_service: ExpenseService = Depends()
) -> ExtractedExpenseDraftResponse:
    """
    Downloads raw image files from provided URLs, runs OCR parsing,
    and returns structured draft expense details.
    """
    gen_response: GenerationResponse = await expense_service.extract_expense_from_urls(
        image_urls=payload.image_urls,
        user_text=payload.user_text,
        current_user_name=payload.current_user_name,
        tier=payload.tier
    )

    return DTOUtils.parse_llm_response(gen_response, ExtractedExpenseDraftResponse)