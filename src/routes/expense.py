# src/routes/expense.py
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from src.dto.agent import GenerationResponse
from src.dto.enums import ExecutionTierEnum
from src.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post(
    "/extract",
    status_code=status.HTTP_200_OK,
    response_model=None,  # <-- Fixes FastAPI dependency resolution error
    summary="Extract draft expense details from receipt files and user prompt"
)
async def extract_expense(
    files: List[UploadFile] = File([], description="Uploaded receipt image or PDF files"),
    user_text: Optional[str] = Form(None, description="Optional notes or contextual text from user"),
    current_user_name: str = Form("Default User", description="Logged in user name context"),
    tier: ExecutionTierEnum = Form(ExecutionTierEnum.TIER_1),
    expense_service: ExpenseService = Depends()
) -> GenerationResponse:
    """
    Accepts raw receipt files along with optional user context strings, extracts OCR,
    and queries the Central AI Service to draft structured expense details.
    """
    response: GenerationResponse = await expense_service.extract_expense_from_receipt(
        files=files,
        user_text=user_text,
        current_user_name=current_user_name,
        tier=tier
    )

    return response