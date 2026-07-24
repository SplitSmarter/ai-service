from typing import Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class PaginationResponse(BaseModel):
    """
    Metadata for paginated API responses.
    """
    total: int = Field(..., description="Total number of available records")
    returned: int = Field(..., description="Number of records returned in this response")
    offset: int = Field(..., description="Starting index of the current page")
    limit: int = Field(..., description="Maximum number of records per page")
    total_pages: Optional[int] = Field(None, description="Total number of pages (if limit > 0)")
    current_page: Optional[int] = Field(None, description="Current page number (derived from offset/limit)")
    has_next: Optional[bool] = Field(None, description="Whether there is a next page available")
    has_previous: Optional[bool] = Field(None, description="Whether there is a previous page available")

    @classmethod
    def build(cls, *, total: int, offset: int, limit: int, returned: int) -> "PaginationResponse":
        """Helper for consistent pagination building."""
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (offset // limit) + 1 if limit > 0 else 1
        has_next = offset + returned < total
        has_previous = offset > 0
        return cls(
            total=total,
            returned=returned,
            offset=offset,
            limit=limit,
            total_pages=total_pages,
            current_page=current_page,
            has_next=has_next,
            has_previous=has_previous,
        )
