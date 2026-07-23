# src/dto/expense.py
from datetime import date
from typing import List, Optional, Union
from pydantic import BaseModel, Field, model_validator

# Enums & Value Objects
class COICOPCategory(BaseModel):
    code: str = Field(description="COICOP classification code (e.g., '01.1.1')")
    name: str = Field(description="COICOP category name (e.g., 'Bread and cereals')")

class PlaceDetails(BaseModel):
    name: Optional[str] = Field(None, description="Extracted store/merchant name or user-saved venue alias")
    city: Optional[str] = Field(None, description="City where transaction occurred")
    state: Optional[str] = Field(None, description="State or province code/name")
    country: Optional[str] = Field(None, description="Country name or ISO code")

class ExtractedItem(BaseModel):
    raw_text: str = Field(description="Cleaned line item text as printed on receipt")
    cpc_keyword: str = Field(description="CPC classification subclass keyword (e.g., 'Dairy products')")
    quantity: int = Field(default=1, description="Quantity purchased")
    unit_cost: float = Field(description="Price per single unit")
    explicit_line_total: Optional[float] = Field(None, description="Explicitly printed total for line item")

class PersonShare(BaseModel):
    name: str = Field(description="Name of the person involved in paying or sharing")
    amount: float = Field(description="Amount associated with person")

# Date & Recurring Schemas
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
    expense_date: Optional[date] = Field(None, description="Transaction date YYYY-MM-DD if fixed expense")
    is_recurring: bool = Field(False, description="True if recurring expense")
    recurring_details: Optional[RecurringDateComponent] = Field(None, description="Populated only if is_recurring is true")

    @model_validator(mode="after")
    def validate_date_details(self) -> "DateComponent":
        if self.is_recurring:
            if self.expense_date is not None:
                raise ValueError("expense_date must be None when is_recurring is True")
            if self.recurring_details is None:
                raise ValueError("recurring_details is required when is_recurring is True")
        else:
            if self.expense_date is None:
                raise ValueError("expense_date is required when is_recurring is False")
            if self.recurring_details is not None:
                raise ValueError("recurring_details must be None when is_recurring is False")
        return self

# Main Extracted LLM Response Structure
class ExtractedExpenseDraftResponse(BaseModel):
    merchant_name: str = Field(description="Extracted merchant name for title")
    description: Optional[str] = Field(None, description="Short summary of expense")
    coicop_category: Optional[COICOPCategory] = Field(None, description="COICOP expenditure classification")
    place_details: Optional[PlaceDetails] = Field(None, description="Extracted place or location details")
    group_name: Optional[str] = Field(None, description="Group name if explicitly mentioned in user context")
    currency: str = Field(default="USD", description="Currency code (e.g. USD, EUR, INR)")
    printed_subtotal: Optional[float] = None
    printed_tax: Optional[float] = None
    printed_grand_total: float = Field(description="Explicit grand total printed on receipt")
    date_details: DateComponent
    paid_by: List[PersonShare] = Field(default_factory=list, description="People who paid for this expense")
    sharers: List[PersonShare] = Field(default_factory=list, description="People sharing this expense")
    items: List[ExtractedItem] = Field(default_factory=list, description="Extracted line items")