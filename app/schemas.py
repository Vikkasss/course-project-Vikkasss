from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class QuoteCreate(BaseModel):
    model_config = {"extra": "forbid", "str_strip_whitespace": True}

    text: str = Field(min_length=1, max_length=2000)
    author: str = Field(min_length=1, max_length=200)
    book: str = Field(min_length=1, max_length=300)

    @field_validator("text", "author", "book")
    @classmethod
    def prevent_empty_strings(cls, v):
        if isinstance(v, str) and not v.strip():
            raise ValueError("field_cannot_be_empty")
        return v


class QuoteResponse(BaseModel):
    id: int
    text: str
    author: str
    book: str
    created_date: datetime


def normalize_datetime(dt: datetime) -> datetime:
    """Нормализация datetime в UTC"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
