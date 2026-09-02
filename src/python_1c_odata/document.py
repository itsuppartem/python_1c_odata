from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from python_1c_odata.entity import EntitySet
from python_1c_odata.posting import PostingMode

_DATE_FIELDS = ("Date", "Дата")
_POSTED_FIELDS = ("Posted", "Проведен")


class Document(EntitySet):
    kind = "Document"

    async def create(
        self,
        data: dict[str, Any],
        *,
        posting_mode: PostingMode = PostingMode.UNPOST,
        timeout: float | None = None,
        data_load_mode: bool | None = None,
    ) -> Any:
        _reject_posted(data)
        if not any(field in data for field in _DATE_FIELDS):
            raise ValueError("Date cannot be empty")
        created = await super().create(data, timeout=timeout, data_load_mode=data_load_mode)
        if posting_mode != PostingMode.UNPOST:
            await self.post(created["Ref_Key"], posting_mode, timeout=timeout)
        return created

    async def edit(
        self,
        key: str | Mapping[str, str],
        data: dict[str, Any],
        *,
        timeout: float | None = None,
        if_match: str | None = None,
        data_load_mode: bool | None = None,
    ) -> Any:
        _reject_posted(data)
        return await super().edit(
            key, data, timeout=timeout, if_match=if_match, data_load_mode=data_load_mode
        )

    async def post(self, key: str, posting_mode: PostingMode, *, timeout: float | None = None) -> Any:
        if posting_mode == PostingMode.UNPOST:
            raise ValueError("use unpost() for unposting")
        if posting_mode == PostingMode.OPER:
            extra = {"PostingModeOperational": "true"}
        elif posting_mode == PostingMode.POST:
            extra = {"PostingModeOperational": "false"}
        else:
            raise ValueError(f"unsupported posting mode: {posting_mode}")
        return await self.infobase.post(
            self.entity,
            key=key,
            action="Post",
            extra=extra,
            timeout=timeout,
        )

    async def unpost(self, key: str, *, timeout: float | None = None) -> Any:
        return await self.infobase.post(self.entity, key=key, action="Unpost", timeout=timeout)


def _reject_posted(data: dict[str, Any]) -> None:
    if any(field in data for field in _POSTED_FIELDS):
        raise ValueError('Do not pass the "Posted" field')
