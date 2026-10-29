"""Upload a local file to the knowledge base via the API.

Usage: python scripts/upload_local.py test_docs/company_policy.txt
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/upload_local.py <file_path>")
        print("Example: python scripts/upload_local.py test_docs/company_policy.txt")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    # Read token from .env
    api_token = ""
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("ADMIN_API_TOKEN="):
                api_token = line.split("=", 1)[1].strip()
                break

    if not api_token:
        print("ADMIN_API_TOKEN not found in .env")
        sys.exit(1)

    base_url = "http://localhost:8000/api/v1"

    print(f"Uploading {file_path.name} ({file_path.stat().st_size} bytes)...")

    with open(file_path, "rb") as f:
        response = httpx.post(
            f"{base_url}/admin/documents/upload",
            files={"file": (file_path.name, f)},
            headers={"Authorization": f"Bearer {api_token}"},
            timeout=30,
        )

    if response.status_code in (200, 201):
        data = response.json()
        print(f"Success! Document ID: {data.get('data', {}).get('document_id', 'unknown')}")
        print(f"Status: {data.get('data', {}).get('status', 'unknown')}")
        print("Worker will now index the document in the background.")
        print("Wait a few seconds, then ask questions in Telegram.")
    else:
        print(f"Error {response.status_code}: {response.text}")


if __name__ == "__main__":
    main()
