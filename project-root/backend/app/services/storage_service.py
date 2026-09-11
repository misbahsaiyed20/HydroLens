"""
Local-disk image storage for Sprint 1 (`uploads/` folder). This is
deliberately isolated behind a small function interface so that swapping to
S3/GCS/Azure Blob later only means changing this one file, not the API layer.
"""
import os
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException

from app.config import get_settings

settings = get_settings()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
# Extension is derived from the validated content-type, never from the
# client-supplied filename — trusting a client filename for the on-disk
# extension is an unnecessary risk (and irrelevant anyway, since the
# filename itself is discarded and replaced with a fresh UUID).
_EXTENSION_BY_CONTENT_TYPE = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def _ensure_upload_dir() -> Path:
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def save_report_image(file: UploadFile, contents: bytes) -> str:
    """
    Validates and persists an uploaded report image to local disk.
    Returns the path relative to UPLOAD_DIR (this is what gets stored in
    Report.image_path — never store an absolute filesystem path).

    Path-traversal safety: the stored filename is always a freshly
    generated UUID + a fixed, content-type-derived extension. The
    client-supplied filename is never used to build a filesystem path, so
    a malicious filename (e.g. "../../etc/passwd", or one containing null
    bytes/path separators) has no way to escape `upload_dir` — it is
    read for its bytes only, never for its name.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type '{file.content_type}'. Allowed: jpeg, png, webp.",
        )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Image exceeds max size of {settings.max_upload_size_mb}MB.",
        )

    upload_dir = _ensure_upload_dir()
    ext = _EXTENSION_BY_CONTENT_TYPE[file.content_type]
    filename = f"{uuid.uuid4()}{ext}"
    destination = upload_dir / filename

    with open(destination, "wb") as f:
        f.write(contents)

    return filename
