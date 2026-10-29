"""Server-side validation for uploaded knowledge documents."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_MAX_FILENAME_LENGTH = 255


class UploadValidationError(ValueError):
    """Base class for upload validation failures."""


class InvalidUploadFilenameError(UploadValidationError):
    """Raised when an upload filename cannot be safely stored."""


class UploadTooLargeError(UploadValidationError):
    """Raised when an uploaded file exceeds the configured server-side limit."""


class UnsupportedUploadTypeError(UploadValidationError):
    """Raised when an uploaded file type is not accepted."""


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    mime_type: str
    file_bytes: bytes


def sanitize_upload_filename(filename: str) -> str:
    """Return a basename-only, control-character-free upload filename."""
    normalized = filename.replace("\\", "/")
    basename = PurePosixPath(normalized).name.strip()
    basename = _CONTROL_CHARS.sub("", basename)
    if basename in {"", ".", ".."}:
        raise InvalidUploadFilenameError("Filename is required")
    if len(basename) > _MAX_FILENAME_LENGTH:
        raise InvalidUploadFilenameError(
            f"Filename must be at most {_MAX_FILENAME_LENGTH} characters"
        )
    return basename


def validate_upload(
    *,
    file_bytes: bytes,
    filename: str,
    mime_type: str,
    max_size_bytes: int,
    allowed_extensions: set[str],
    allowed_mime_types: set[str],
) -> ValidatedUpload:
    """Validate upload bytes, filename, size, and type."""
    safe_filename = sanitize_upload_filename(filename)
    normalized_mime = mime_type or "application/octet-stream"

    if len(file_bytes) > max_size_bytes:
        raise UploadTooLargeError(f"File exceeds the {max_size_bytes} byte upload limit")

    suffix = PurePosixPath(safe_filename).suffix.lower()
    extension_allowed = suffix in allowed_extensions
    if normalized_mime == "application/octet-stream":
        mime_allowed = extension_allowed and normalized_mime in allowed_mime_types
    else:
        mime_allowed = normalized_mime in allowed_mime_types
    if not extension_allowed and not mime_allowed:
        raise UnsupportedUploadTypeError(
            f"Unsupported upload type: {safe_filename} ({normalized_mime})"
        )

    return ValidatedUpload(
        filename=safe_filename,
        mime_type=normalized_mime,
        file_bytes=file_bytes,
    )
