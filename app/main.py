from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.errors import ERROR_MAP, ProblemDetailException, problem_detail_handler
from app.file_security import MAX_FILE_SIZE, secure_file_save
from app.quotes import _DB_QUOTES
from app.schemas import QuoteCreate, normalize_datetime

app = FastAPI(title="SecDev Course App", version="0.1.0")
app.add_exception_handler(ProblemDetailException, problem_detail_handler)


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    error_info = ERROR_MAP.get(exc.code, {"type": "about:blank", "title": "Error"})
    return JSONResponse(
        status_code=exc.status,
        content={
            "type": error_info["type"],
            "title": error_info["title"],
            "status": exc.status,
            "detail": exc.message,
            "correlation_id": str(uuid4()),
            "instance": str(request.url),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


_DB = {"items": []}


@app.post("/items")
def create_item(name: str):
    if not name or len(name) > 100:
        raise ProblemDetailException(
            status=422,
            title="Validation Failed",
            detail="Name must be between 1 and 100 characters",
            error_type="/errors/validation",
        )
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ProblemDetailException(
        status=404,
        title="Not Found",
        detail="Item not found",
        error_type="/errors/not-found",
    )


@app.get("/quotes")
def get_quotes():
    return _DB_QUOTES["quotes"]


@app.get("/quotes/{quote_id}")
def get_quote(quote_id: int):
    for quote in _DB_QUOTES["quotes"]:
        if quote["id"] == quote_id:
            return quote
    raise ProblemDetailException(
        status=404,
        title="Not Found",
        detail="Quote not found",
        error_type="/errors/not-found",
    )


@app.get("/quotes/book/{book_name}")
def get_quote_from_book(book_name: str):
    for quote in _DB_QUOTES["quotes"]:
        quotes_by_book = [
            quote for quote in _DB_QUOTES["quotes"] if quote["book"] == book_name
        ]
        if not quotes_by_book:
            raise ProblemDetailException(
                status=404,
                title="Not Found",
                detail=f"No quotes found for book: {book_name}",
                error_type="/errors/not-found",
            )
        return quotes_by_book


@app.post("/quotes")
def create_quote(quote: QuoteCreate):
    new_quote = {
        "id": len(_DB_QUOTES["quotes"]) + 1,
        "text": quote.text,
        "author": quote.author,
        "book": quote.book,
        "created_date": normalize_datetime(datetime.now()),
    }
    _DB_QUOTES["quotes"].append(new_quote)
    return new_quote


@app.delete("/quotes/{quote_id}")
def delete_quote(quote_id: int):
    for i, quote in enumerate(_DB_QUOTES["quotes"]):
        if quote["id"] == quote_id:
            deleted_quote = _DB_QUOTES["quotes"].pop(i)
            return {"message": "Quote deleted", "quote": deleted_quote}
    raise ProblemDetailException(
        status=404,
        title="Not Found",
        detail="Quote not found",
        error_type="/errors/not-found",
    )


@app.post("/upload-cover")
async def upload_book_cover(file: UploadFile = File(...)):
    try:
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        saved_path = secure_file_save(upload_dir, file)
        return {"filename": saved_path.name, "message": "File uploaded securely"}

    except ValueError as e:

        error_msg = str(e)

        if error_msg == "file_too_large":

            raise ProblemDetailException(
                status=413,
                title="File Too Large",
                detail=f"File size exceeds {MAX_FILE_SIZE} bytes",
                error_type="/errors/validation",
            ) from e  # ← ДОБАВЬ 'from e'

        elif error_msg == "invalid_file_type":

            raise ProblemDetailException(
                status=415,
                title="Unsupported Media Type",
                detail="File type not allowed",
                error_type="/errors/validation",
            ) from e

        else:

            raise ProblemDetailException(
                status=400,
                title="Bad Request",
                detail="Invalid file upload",
                error_type="/errors/validation",
            ) from e
