from datetime import datetime

from pydantic import BaseModel


class Quote(BaseModel):
    id: int
    text: str
    author: str
    book: str
    created_date: datetime


class QuoteCreate(BaseModel):
    text: str
    author: str
    book: str


# temporary database
_DB_QUOTES = {"quotes": []}
