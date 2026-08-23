"""OData 3.0 literals used by 1C (v4 dropped guid'...' / datetime'...')."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID


def parse_guid(value: str) -> str:
    return str(UUID(str(value)))


def odata_datetime(value: datetime | date | str) -> str:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("datetime'") and stripped.endswith("'"):
            return stripped
        return f"datetime'{stripped}'"
    if isinstance(value, datetime):
        return f"datetime'{value.strftime('%Y-%m-%dT%H:%M:%S')}'"
    if isinstance(value, date):
        return f"datetime'{value.isoformat()}T00:00:00'"
    raise TypeError(f"unsupported datetime value: {value!r}")
