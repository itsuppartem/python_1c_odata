"""Errors raised for failed 1C OData HTTP responses."""

from __future__ import annotations

import json


class ODataError(Exception):
    def __init__(self, status: int, message: str, body: str | None = None) -> None:
        self.status = status
        self.message = message
        self.body = body
        super().__init__(f"HTTP {status}: {message}")


def error_from_response(status: int, text: str) -> ODataError:
    message = text or f"HTTP {status}"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return ODataError(status, message, body=text)
    err = payload.get("odata.error") or payload.get("error") or {}
    raw = err.get("message")
    if isinstance(raw, dict):
        message = str(raw.get("value") or message)
    elif isinstance(raw, str) and raw:
        message = raw
    return ODataError(status, message, body=text)
