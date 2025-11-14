from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse


class ProblemDetailException(Exception):
    def __init__(
        self,
        status: int,
        title: str,
        detail: str,
        error_type: str = "about:blank",
        instance: str = None,
    ):
        self.status = status
        self.title = title
        self.detail = detail
        self.type = error_type
        self.instance = instance
        self.correlation_id = str(uuid4())


def problem_detail_handler(request: Request, exc: ProblemDetailException):
    content = {
        "type": exc.type,
        "title": exc.title,
        "status": exc.status,
        "detail": exc.detail,
        "correlation_id": exc.correlation_id,
        "instance": exc.instance or str(request.url),
    }
    return JSONResponse(status_code=exc.status, content=content)


ERROR_MAP = {
    "validation_error": {"type": "/errors/validation", "title": "Validation Failed"},
    "not_found": {"type": "/errors/not-found", "title": "Resource Not Found"},
    "rate_limit": {"type": "/errors/rate-limit", "title": "Rate Limit Exceeded"},
}
