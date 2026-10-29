"""Server-side upload validation tests."""

from __future__ import annotations

import pytest

from app.domain.services.upload_validation import (
    InvalidUploadFilenameError,
    UnsupportedUploadTypeError,
    UploadTooLargeError,
    sanitize_upload_filename,
    validate_upload,
)


class FakeUploadFile:
    def __init__(
        self,
        *,
        filename: str,
        content_type: str,
        chunks: list[bytes],
    ) -> None:
        self.filename = filename
        self.content_type = content_type
        self._chunks = chunks

    async def read(self, size: int = -1) -> bytes:
        if not self._chunks:
            return b""
        return self._chunks.pop(0)


class TestUploadValidation:
    def test_sanitizes_path_like_filename(self) -> None:
        assert sanitize_upload_filename(r"C:\Users\me\policy.pdf") == "policy.pdf"
        assert sanitize_upload_filename("../docs/hr.md") == "hr.md"

    def test_rejects_empty_filename_after_sanitizing(self) -> None:
        with pytest.raises(InvalidUploadFilenameError):
            sanitize_upload_filename("///")

    def test_rejects_files_over_server_side_size_limit(self) -> None:
        with pytest.raises(UploadTooLargeError):
            validate_upload(
                file_bytes=b"12345",
                filename="policy.txt",
                mime_type="text/plain",
                max_size_bytes=4,
                allowed_extensions={".txt"},
                allowed_mime_types={"text/plain"},
            )

    def test_rejects_unsupported_extension_and_mime_type(self) -> None:
        with pytest.raises(UnsupportedUploadTypeError):
            validate_upload(
                file_bytes=b"hello",
                filename="payload.exe",
                mime_type="application/x-msdownload",
                max_size_bytes=100,
                allowed_extensions={".txt"},
                allowed_mime_types={"text/plain"},
            )

    def test_rejects_unknown_extension_even_with_octet_stream_mime(self) -> None:
        with pytest.raises(UnsupportedUploadTypeError):
            validate_upload(
                file_bytes=b"hello",
                filename="payload.exe",
                mime_type="application/octet-stream",
                max_size_bytes=100,
                allowed_extensions={".txt"},
                allowed_mime_types={"application/octet-stream", "text/plain"},
            )

    def test_allows_known_extension_when_browser_uses_octet_stream(self) -> None:
        result = validate_upload(
            file_bytes=b"# FAQ",
            filename="faq.md",
            mime_type="application/octet-stream",
            max_size_bytes=100,
            allowed_extensions={".md"},
            allowed_mime_types={"text/markdown"},
        )

        assert result.filename == "faq.md"
        assert result.mime_type == "application/octet-stream"

    async def test_stream_reader_rejects_file_once_limit_is_exceeded(self) -> None:
        from app.api.uploads import read_upload_file

        upload = FakeUploadFile(
            filename="policy.txt",
            content_type="text/plain",
            chunks=[b"12", b"345"],
        )

        with pytest.raises(UploadTooLargeError):
            await read_upload_file(
                upload,
                max_size_bytes=4,
                allowed_extensions={".txt"},
                allowed_mime_types={"text/plain"},
            )

    async def test_stream_reader_returns_sanitized_filename(self) -> None:
        from app.api.uploads import read_upload_file

        upload = FakeUploadFile(
            filename="../policy.txt",
            content_type="text/plain",
            chunks=[b"hello"],
        )

        result = await read_upload_file(
            upload,
            max_size_bytes=10,
            allowed_extensions={".txt"},
            allowed_mime_types={"text/plain"},
        )

        assert result.filename == "policy.txt"
        assert result.file_bytes == b"hello"
