from __future__ import annotations

import uuid

from app.api import admin_routes


def test_admin_routes_uuid_annotations_are_available_at_runtime() -> None:
    assert admin_routes.uuid.UUID is uuid.UUID
