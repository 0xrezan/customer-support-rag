"""Upload-file helpers shared by admin routes."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.services.upload_validation import (
    ValidatedUpload,
    validate_upload,
)

_READ_CHUNK_SIZE_BYTES = 1024 * 1024


@dataclass(frozen=True)
class ReadUploadResult:
    filename: str
    mime_type: str
    file_bytes: bytes


async def read_upload_file(
    file: object,
    *,
    max_size_bytes: int,
    allowed_extensions: set[str],
    allowed_mime_types: set[str],
) -> ReadUploadResult:
    """Read an UploadFile in chunks and validate it before registration."""
    filename = getattr(file, "filename", "") or ""
    mime_type = getattr(file, "content_type", "") or "application/octet-stream"

    # Validate metadata before reading the body so unsupported files fail early.
    validate_upload(
        file_bytes=b"",
        filename=filename,
        mime_type=mime_type,
        max_size_bytes=max_size_bytes,
        allowed_extensions=allowed_extensions,
        allowed_mime_types=allowed_mime_types,
    )

    chunks: list[bytes] = []
    total_size = 0
    while True:
        chunk = await file.read(_READ_CHUNK_SIZE_BYTES)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_size_bytes:
            validate_upload(
                file_bytes=b"x" * (max_size_bytes + 1),
                filename=filename,
                mime_type=mime_type,
                max_size_bytes=max_size_bytes,
                allowed_extensions=allowed_extensions,
                allowed_mime_types=allowed_mime_types,
            )
        chunks.append(chunk)

    validated: ValidatedUpload = validate_upload(
        file_bytes=b"".join(chunks),
        filename=filename,
        mime_type=mime_type,
        max_size_bytes=max_size_bytes,
        allowed_extensions=allowed_extensions,
        allowed_mime_types=allowed_mime_types,
    )
    return ReadUploadResult(
        filename=validated.filename,
        mime_type=validated.mime_type,
        file_bytes=validated.file_bytes,
    )
