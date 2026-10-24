# src/dto/expense/expense.py
from datetime import date
from enum import StrEnum
from typing import List, Optional, Union

from pydantic import BaseModel, Field, model_validator

from src.dto.enums import UserTierEnum


class ReceiptAdjustmentKind(StrEnum):
    TAX = "TAX"
    TIP = "TIP"
    FEE = "FEE"
    DISCOUNT = "DISCOUNT"
    ROUNDING = "ROUNDING"
    OTHER = "OTHER"


class COICOPCategory(BaseModel):
    code: str = Field(description="COICOP classification code (e.g., '01.1.1')")
    name: str = Field(description="COICOP category name (e.g., 'Bread and cereals')")
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Model confidence 0..1"
    )


class ClassificationHint(BaseModel):
    code: Optional[str] = Field(None, description="Taxonomy code when known")
    keyword: Optional[str] = Field(None, description="Subclass keyword / name")
    name: Optional[str] = Field(None, description="Human-readable name")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class PlaceDetails(BaseModel):
    name: Optional[str] = Field(None, description="Store/venue name")
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = Field(None, description="ISO 3166-1 alpha-2")
    address: Optional[str] = None
    match_keywords: List[str] = Field(default_factory=list)
    search_queries: List[str] = Field(
        default_factory=list,
        description="Preference-ordered geo/DB search queries",
    )


class MerchantDetails(BaseModel):
    name: Optional[str] = Field(None, description="Brand / store name if present")
    merchant_alias: List[str] = Field(default_factory=list, description="Other matching names of the merchant")
    mcc_hint: Optional[str] = Field(None, description="MCC only if explicitly printed")


class ReceiptAdjustment(BaseModel):
    kind: ReceiptAdjustmentKind
    amount: float = Field(..., gt=0, description="Absolute printed magnitude")
    raw_label: str = Field(..., description="Printed label e.g. 'CGST 9%'")


class ExtractedItem(BaseModel):
    raw_text: str = Field(description="Cleaned merchandise line text")
    cpc_keyword: str = Field(
        default="",
        description="CPC subclass keyword (legacy; prefer cpc.keyword)",
    )
    quantity: int = Field(
        default=1,
        ge=1,
        description=(
            "Printed quantity when present on the line (Qty, xN, N x, @); "
            "use 1 only when quantity is not printed — never invent from totals"
        ),
    )
    unit_cost: Optional[float] = Field(
        None, description="Printed unit price; omit if only line total exists"
    )
    explicit_line_total: Optional[float] = Field(
        None, description="Explicitly printed total for line item"
    )
    cpc: Optional[ClassificationHint] = None
    coicop: Optional[ClassificationHint] = None
    item_name_candidates: List[str] = Field(
        default_factory=list,
        description="Preference-ordered names for catalog search",
    )
    match_keywords: List[str] = Field(default_factory=list)


class PersonShare(BaseModel):
    name: str = Field(description="Name of the person involved in paying or sharing")
    amount: float = Field(description="Amount associated with person")


class DateWeekly(BaseModel):
    weekday: str


class DateMonthly(BaseModel):
    day: int


class DateYearly(BaseModel):
    day: int
    month: str


class DateCustom(BaseModel):
    day: int


DateComponentUnion = Union[DateWeekly, DateMonthly, DateYearly, DateCustom]


class RecurringDateComponent(BaseModel):
    recurring_period: str = Field(description="daily, weekly, monthly, yearly, custom")
    custom_period_duration: Optional[int] = None
    interval: int = 1
    selected_values: List[DateComponentUnion]


class DateComponent(BaseModel):
    expense_date: Optional[date] = Field(
        None, description="Transaction date YYYY-MM-DD if known"
    )
    is_recurring: bool = Field(False, description="True only if user notes request recurring")
    recurring_details: Optional[RecurringDateComponent] = Field(
        None, description="Populated only if is_recurring is true"
    )

    @model_validator(mode="after")
    def validate_date_details(self) -> "DateComponent":
        if self.is_recurring:
            if self.expense_date is not None:
                raise ValueError("expense_date must be None when is_recurring is True")
            if self.recurring_details is None:
                raise ValueError("recurring_details is required when is_recurring is True")
        else:
            if self.recurring_details is not None:
                raise ValueError(
                    "recurring_details must be None when is_recurring is False"
                )
        return self


class ExtractedExpenseDraftResponse(BaseModel):
    """Shared receipt facts for expense and transfer drafting (not create DTOs)."""

    title: Optional[str] = Field(
        None, description="Optional short title distinct from merchant"
    )
    merchant_name: Optional[str] = Field(
        None, description="Legacy merchant title; prefer merchant.name"
    )
    merchant: Optional[MerchantDetails] = None
    description: Optional[str] = Field(
        None, description="Short summary without digits when possible"
    )
    coicop_category: Optional[COICOPCategory] = None
    category_name_candidates: List[str] = Field(default_factory=list)
    place_details: Optional[PlaceDetails] = None
    group_name: Optional[str] = None
    counterparty_user_name: Optional[str] = Field(
        None, description="P2P counterparty when not a store"
    )
    payment_method_hint: Optional[str] = Field(
        None,
        description="Rail only: upi/card/cash/wallet/bank or short printed word; no account ids",
    )
    currency: Optional[str] = Field(
        None, description="ISO 4217 when detectable"
    )
    printed_subtotal: Optional[float] = None
    printed_grand_total: float = Field(
        description="Explicit grand total / amount due printed on receipt"
    )
    adjustments: List[ReceiptAdjustment] = Field(
        default_factory=list,
        description="One entry per printed non-merchandise money row",
    )
    date_details: DateComponent = Field(
        default_factory=lambda: DateComponent(is_recurring=False, expense_date=None)
    )
    paid_by: List[PersonShare] = Field(
        default_factory=list,
        description="Only if names appear in OCR or user notes; else empty",
    )
    sharers: List[PersonShare] = Field(
        default_factory=list,
        description="Only if names appear in OCR or user notes; else empty",
    )
    items: List[ExtractedItem] = Field(
        default_factory=list,
        description="Merchandise lines only (not tax/tip/fee/total)",
    )


class ExtractFromUrlsRequest(BaseModel):
    image_urls: List[str] = Field(..., description="List of remote image URLs to process")
    user_text: Optional[str] = Field(None, description="Optional notes or contextual text from user")
    current_user_name: str = Field("Default User", description="Logged-in user name")
    tier: UserTierEnum = Field(UserTierEnum.TIER_2, description="Execution tier")
