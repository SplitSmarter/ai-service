# src/routes/expense.py
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from src.dto.llm.agent import GenerationResponse
from src.dto.enums import UserTierEnum
from src.dto.expense.expense import ExtractedExpenseDraftResponse, ExtractFromUrlsRequest
from src.dto.base import SuccessResponse
from src.services.expense_service import ExpenseService
from src.utils.dto_util import DTOUtils

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post(
    "/extract",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[ExtractedExpenseDraftResponse, None],
    summary="Extract draft expense details from receipt files and user prompt"
)
async def extract_expense(
    files: List[UploadFile] = File([], description="Uploaded receipt image or PDF files"),
    user_text: Optional[str] = Form(None, description="Optional notes or contextual text from user"),
    current_user_name: str = Form("Default User", description="Logged in user name context"),
    tier: UserTierEnum = Form(UserTierEnum.TIER_1),
    expense_service: ExpenseService = Depends()
) -> SuccessResponse[ExtractedExpenseDraftResponse, None]:
    """
    Accepts raw receipt files along with optional user context strings, extracts OCR,
    and returns structured draft expense details wrapped in SuccessResponse.
    """
    gen_response: GenerationResponse = await expense_service.extract_expense_from_receipt(
        files=files,
        user_text=user_text,
        current_user_name=current_user_name,
        tier=tier
    )

    draft_data = DTOUtils.parse_llm_response(gen_response, ExtractedExpenseDraftResponse)

    return SuccessResponse(
        message="Expense details extracted successfully",
        data=draft_data
    )


@router.post(
    "/extract-from-urls",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[ExtractedExpenseDraftResponse, None],
    summary="Test endpoint: Extract expense details from a list of remote image URLs"
)
async def extract_expense_from_urls(
    payload: ExtractFromUrlsRequest,
    expense_service: ExpenseService = Depends()
) -> SuccessResponse[ExtractedExpenseDraftResponse, None]:
    """
    Downloads raw image files from provided URLs, runs OCR parsing,
    and returns structured draft expense details wrapped in SuccessResponse.
    """
    gen_response: GenerationResponse = await expense_service.extract_expense_from_urls(
        image_urls=payload.image_urls,
        user_text=payload.user_text,
        current_user_name=payload.current_user_name,
        tier=payload.tier
    )

    draft_data = DTOUtils.parse_llm_response(gen_response, ExtractedExpenseDraftResponse)

    return SuccessResponse(
        message="Expense details extracted successfully from URLs",
        data=draft_data
    )