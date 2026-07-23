# src/routes/ai_router.py
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from src.config.config import get_request_logger
from src.dto.agent import GenerationRequest, GenerationResponse
from src.dto.ocr import OCRRequest, OCRResponse
from src.services.central_ai_service import CentralAIService

router = APIRouter(prefix="/v1/ai", tags=["Central Core AI Gateway"])


@router.post("/generate", response_model=GenerationResponse)
async def process_balanced_inference(
        payload: GenerationRequest,
):
    ai_service = CentralAIService()
    return await ai_service.execute_inference(payload)


@router.post("/ocr/file", response_model=OCRResponse)
async def process_ocr_upload(
        file: UploadFile = File(...),
):
    """Processes an uploaded image file using Google Cloud Vision OCR."""
    ai_service = CentralAIService()
    image_bytes = await file.read()
    request = OCRRequest(image_bytes=image_bytes)
    return await ai_service.execute_ocr(request)


@router.post("/ocr/path", response_model=OCRResponse)
async def process_ocr_path(
        payload: OCRRequest,
):
    """Processes an image from a local server file path."""
    ai_service = CentralAIService()
    return await ai_service.execute_ocr(payload)