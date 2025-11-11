from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.quotes import _DB_QUOTES, QuoteCreate

app = FastAPI(title="SecDev Course App", version="0.1.0")


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Normalize FastAPI HTTPException into our error envelope
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# Example minimal entity (for tests/demo)
_DB = {"items": []}


@app.post("/items")
def create_item(name: str):
    if not name or len(name) > 100:
        raise ApiError(
            code="validation_error", message="name must be 1..100 chars", status=422
        )
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(code="not_found", message="item not found", status=404)


@app.get("/quotes")
def get_quotes():
    return _DB_QUOTES["quotes"]


@app.get("/quotes/{quote_id}")
def get_quote(quote_id: int):
    for quote in _DB_QUOTES["quotes"]:
        if quote["id"] == quote_id:
            return quote
    raise ApiError(code="not_found", message="quote not found", status=404)


@app.get("/quotes/book/{book_name}")
def get_quote_from_book(book_name: str):
    for quote in _DB_QUOTES["quotes"]:
        quotes_by_book = [
            quote for quote in _DB_QUOTES["quotes"] if quote["book"] == book_name
        ]
        if not quotes_by_book:
            raise ApiError(
                code="not_found", message=f"No quotes found for book: {book_name}"
            )
        return quotes_by_book


@app.post("/quotes")
def create_quote(quote: QuoteCreate):
    new_quote = {
        "id": len(_DB_QUOTES["quotes"]) + 1,
        "text": quote.text,
        "author": quote.author,
        "book": quote.book,
        "created_date": datetime.now(),
    }
    _DB_QUOTES["quotes"].append(new_quote)
    return new_quote


@app.delete("/quotes/{quote_id}")
def delete_quote(quote_id: int):
    for i, quote in enumerate(_DB_QUOTES["quotes"]):
        if quote["id"] == quote_id:
            deleted_quote = _DB_QUOTES["quotes"].pop(i)
            return {"message": "Quote deleted", "quote": deleted_quote}
    raise ApiError(code="not_found", message="Quote not found")
