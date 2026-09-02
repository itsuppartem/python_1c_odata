from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from python_1c_odata.entity import EntitySet


class DocumentJournal(EntitySet):
    """1C document journal. Standard OData exposes query/get only."""

    kind = "DocumentJournal"

    async def create(self, data: dict[str, Any], *, timeout: float | None = None) -> Any:
        raise TypeError("DocumentJournal is read-only over OData")

    async def edit(
        self,
        key: str | Mapping[str, str],
        data: dict[str, Any],
        *,
        timeout: float | None = None,
        if_match: str | None = None,
    ) -> Any:
        raise TypeError("DocumentJournal is read-only over OData")

    async def replace(
        self,
        key: str | Mapping[str, str],
        data: dict[str, Any],
        *,
        timeout: float | None = None,
        if_match: str | None = None,
    ) -> Any:
        raise TypeError("DocumentJournal is read-only over OData")

    async def delete(
        self,
        key: str | Mapping[str, str],
        *,
        timeout: float | None = None,
        if_match: str | None = None,
    ) -> Any:
        raise TypeError("DocumentJournal is read-only over OData")
