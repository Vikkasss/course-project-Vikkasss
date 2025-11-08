import uuid
from pathlib import Path

from fastapi import UploadFile

# Константы безопасности
MAX_FILE_SIZE = 10_000_000  # 10MB
ALLOWED_MIME_TYPES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "application/pdf": [b"%PDF"],
}


def sniff_signature(data: bytes) -> str:
    """Проверка magic bytes файла"""
    for mime_type, signatures in ALLOWED_MIME_TYPES.items():
        for signature in signatures:
            if data.startswith(signature):
                return mime_type
    return None


def secure_file_save(upload_dir: Path, file: UploadFile) -> Path:
    """Безопасное сохранение файла"""
    # Чтение данных с лимитом
    data = file.file.read(MAX_FILE_SIZE + 1)
    if len(data) > MAX_FILE_SIZE:
        raise ValueError("file_too_large")

    # Проверка сигнатуры
    mime_type = sniff_signature(data)
    if not mime_type:
        raise ValueError("invalid_file_type")

    # Канонизация пути
    upload_dir = upload_dir.resolve(strict=True)

    # Генерация безопасного имени
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "application/pdf": ".pdf"}.get(
        mime_type, ".bin"
    )

    filename = f"{uuid.uuid4()}{ext}"
    file_path = (upload_dir / filename).resolve()

    # Защита от path traversal
    if not str(file_path).startswith(str(upload_dir)):
        raise ValueError("path_traversal_attempt")

    # Проверка симлинков в пути
    for parent in file_path.parents:
        if parent.is_symlink():
            raise ValueError("symlink_in_path")

    # Сохранение файла
    file_path.write_bytes(data)
    return file_path
