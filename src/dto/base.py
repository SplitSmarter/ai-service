from typing import Generic, TypeVar, Optional
from pydantic import field_validator, BaseModel
from src.dto.pagination import PaginationResponse
from src.utils.translation.TranslationUtil import _

T = TypeVar("T")
M = TypeVar("M")

class SuccessResponse(BaseModel, Generic[T, M]):
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    pagination: Optional[PaginationResponse] = None
    meta: Optional[M] = None

    @field_validator("message")
    @classmethod
    def translate_message(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return _(v)
        return v

class ErrorResponse(BaseModel, Generic[T, M]):
    success: bool = False
    message: Optional[str] = None
    error: Optional[T] = None
    meta: Optional[M] = None

    @field_validator("message")
    @classmethod
    def translate_message(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return _(v)
        return v