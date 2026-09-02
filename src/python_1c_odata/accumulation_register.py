from __future__ import annotations

from datetime import date, datetime
from typing import Any

from python_1c_odata.entity import EntitySet
from python_1c_odata.filter import Filter
from python_1c_odata.literals import odata_datetime
from python_1c_odata.url import accumulation_virtual_path


class AccumulationRegister(EntitySet):
    kind = "AccumulationRegister"

    async def balance(
        self,
        period: datetime | date | str | None = None,
        condition: str | Filter | None = None,
        *,
        select: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        return await self._virtual(
            "Balance",
            period=period,
            condition=condition,
            select=select,
            timeout=timeout,
        )

    async def turnovers(
        self,
        start_period: datetime | date | str | None = None,
        end_period: datetime | date | str | None = None,
        condition: str | Filter | None = None,
        *,
        select: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        return await self._virtual(
            "Turnovers",
            start_period=start_period,
            end_period=end_period,
            condition=condition,
            select=select,
            timeout=timeout,
        )

    async def balance_and_turnovers(
        self,
        start_period: datetime | date | str | None = None,
        end_period: datetime | date | str | None = None,
        condition: str | Filter | None = None,
        *,
        select: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        return await self._virtual(
            "BalanceAndTurnovers",
            start_period=start_period,
            end_period=end_period,
            condition=condition,
            select=select,
            timeout=timeout,
        )

    async def _virtual(
        self,
        function: str,
        *,
        period: datetime | date | str | None = None,
        start_period: datetime | date | str | None = None,
        end_period: datetime | date | str | None = None,
        condition: str | Filter | None = None,
        select: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        path = accumulation_virtual_path(
            self.infobase.root,
            self.entity,
            function,
            period=None if period is None else odata_datetime(period),
            start_period=None if start_period is None else odata_datetime(start_period),
            end_period=None if end_period is None else odata_datetime(end_period),
            condition=None if condition is None else str(condition),
        )
        url = path + self.infobase.odata_query_string(select=select)
        return await self.infobase.request("GET", url, timeout=timeout)
