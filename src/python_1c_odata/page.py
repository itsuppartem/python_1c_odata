"""One OData collection page (``value`` + optional ``$inlinecount``)."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any


class Page(Mapping[str, Any]):
    """Dict-compatible wrapper around a collection payload."""

    def __init__(self, payload: Mapping[str, Any]) -> None:
        self._payload = dict(payload)
        raw = payload.get("value", [])
        self.value: list[Any] = list(raw) if isinstance(raw, list) else []
        self.count = _inline_count(payload)

    def __getitem__(self, key: str) -> Any:
        return self._payload[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._payload)

    def __len__(self) -> int:
        return len(self._payload)

    def __repr__(self) -> str:
        return f"Page(rows={len(self.value)}, count={self.count!r})"


def _inline_count(payload: Mapping[str, Any]) -> int | None:
    for key in ("__count", "odata.count", "@odata.count"):
        if key in payload and payload[key] is not None:
            return int(payload[key])
    return None
