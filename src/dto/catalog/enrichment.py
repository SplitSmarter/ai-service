from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ClassificationCandidate(BaseModel):
    code: str = Field(..., description="Classification code (e.g., '01.1.1' or '21111')")
    title: str = Field(..., description="Official title/description of the classification candidate")
    score: Optional[float] = Field(None, description="Similarity or retrieval score")


class RawProductInput(BaseModel):
    title: str = Field(..., description="Raw title of the product from vendor/scraper")
    barcode: Optional[str] = Field(None, description="Product barcode (EAN/UPC)")
    category: Optional[str] = Field(None, description="Raw category breadcrumbs from retailer")
    manufacturer: Optional[str] = Field(None, description="Manufacturer or brand name from raw source")
    image_url: Optional[str] = Field(None, description="Product image URL")
    product_url: Optional[str] = Field(None, description="Product source link")
    candidate_coicop_codes: List[ClassificationCandidate] = Field(
        default_factory=list, description="Top candidate COICOP codes retrieved via search"
    )
    candidate_cpc_codes: List[ClassificationCandidate] = Field(
        default_factory=list, description="Top candidate CPC codes retrieved via search"
    )


class EnrichProductsBatchRequest(BaseModel):
    products: List[RawProductInput] = Field(..., min_items=1, max_items=50)


class GeneratedKeywordItem(BaseModel):
    keyword: str = Field(..., description="Extracted search keyword")
    keyword_type: str = Field(
        ...,
        description="Type of keyword: 'PRIMARY', 'BRAND', 'BRAND_VARIANT', 'SYNONYM', 'GENERIC', 'SLANG', 'MISSPELLING'",
    )


class EnrichedProductItem(BaseModel):
    barcode: Optional[str] = Field(None, description="Original barcode for correlation")
    raw_title: str = Field(..., description="Original raw title passed in request")
    canonical_name: str = Field(..., description="Clean, standardized product name")
    brand: Optional[str] = Field(None, description="Cleaned, extracted brand name")

    # Classifications & Fallback Audit
    coicop_code: Optional[str] = Field(
        None, description="Selected or self-generated COICOP code (e.g., '06.1.3')"
    )
    is_coicop_from_candidates: bool = Field(
        True, description="True if coicop_code matched a provided candidate; False if generated autonomously"
    )
    cpc_code: Optional[str] = Field(
        None, description="Selected or self-generated CPC code (e.g., '35260')"
    )
    is_cpc_from_candidates: bool = Field(
        True, description="True if cpc_code matched a provided candidate; False if generated autonomously"
    )

    custom_app_category: Optional[str] = Field(None, description="Simplified user-facing app category")

    # Financial Hints
    default_currency: str = Field(
        "USD", description="3-letter ISO currency code inferred from product context (e.g., 'INR', 'USD', 'EUR')"
    )
    typical_price_min: Optional[float] = Field(
        None, description="Estimated typical minimum price in local currency"
    )
    typical_price_max: Optional[float] = Field(
        None, description="Estimated typical maximum price in local currency"
    )
    default_vat_rate: Optional[float] = Field(
        None, description="Estimated standard VAT/GST/Tax percentage applicable (e.g., 18.0 for 18% GST)"
    )

    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")
    reasoning: Optional[str] = Field(None, description="Brief justification for classification & financial choices")
    keywords: List[GeneratedKeywordItem] = Field(default_factory=list, description="Generated search keywords")


class EnrichProductsBatchResponse(BaseModel):
    enriched_products: List[EnrichedProductItem]