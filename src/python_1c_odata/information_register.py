from __future__ import annotations

from datetime import date, datetime
from typing import Any

from python_1c_odata.client import Infobase
from python_1c_odata.entity import EntitySet
from python_1c_odata.filter import Filter
from python_1c_odata.literals import odata_datetime
from python_1c_odata.url import slice_path


class InformationRegister(EntitySet):
    kind = "InformationRegister"

    def __init__(self, infobase: Infobase, name: str, *, record_type: bool = False) -> None:
        super().__init__(infobase, name)
        self.record_type = record_type

    @property
    def entity(self) -> str:
        base = super().entity
        return f"{base}_RecordType" if self.record_type else base

    async def slice_last(
        self,
        period: datetime | date | str | None = None,
        condition: str | Filter | None = None,
        *,
        select: str | None = None,
        orderby: str | None = None,
        expand: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        return await self._slice(
            "SliceLast",
            period,
            condition,
            select=select,
            orderby=orderby,
            expand=expand,
            timeout=timeout,
        )

    async def slice_first(
        self,
        period: datetime | date | str | None = None,
        condition: str | Filter | None = None,
        *,
        select: str | None = None,
        orderby: str | None = None,
        expand: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        return await self._slice(
            "SliceFirst",
            period,
            condition,
            select=select,
            orderby=orderby,
            expand=expand,
            timeout=timeout,
        )

    async def _slice(
        self,
        function: str,
        period: datetime | date | str | None,
        condition: str | Filter | None,
        *,
        select: str | None,
        orderby: str | None,
        expand: str | None,
        timeout: float | None,
    ) -> Any:
        path = slice_path(
            self.infobase.root,
            self.entity,
            function,
            period=None if period is None else odata_datetime(period),
            condition=None if condition is None else str(condition),
        )
        url = path + self.infobase.odata_query_string(select=select, orderby=orderby, expand=expand)
        return await self.infobase.request("GET", url, timeout=timeout)
