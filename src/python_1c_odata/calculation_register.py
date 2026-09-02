from __future__ import annotations

from typing import Any

from python_1c_odata.entity import EntitySet
from python_1c_odata.filter import Filter
from python_1c_odata.url import calculation_virtual_path, query_string


class CalculationRegister(EntitySet):
    kind = "CalculationRegister"

    async def schedule_data(
        self,
        condition: str | Filter | None = None,
        *,
        select: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        return await self._virtual(
            "ScheduledData",
            condition=condition,
            select=select,
            timeout=timeout,
        )

    async def actual_action_period(
        self,
        condition: str | Filter | None = None,
        *,
        select: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        return await self._virtual(
            "ActualActionPeriod",
            condition=condition,
            select=select,
            timeout=timeout,
        )

    async def _virtual(
        self,
        function: str,
        *,
        condition: str | Filter | None,
        select: str | None,
        timeout: float | None,
    ) -> Any:
        path = calculation_virtual_path(
            self.infobase.root,
            self.entity,
            function,
            condition=None if condition is None else str(condition),
        )
        url = path + query_string(select=select)
        return await self.infobase.request("GET", url, timeout=timeout)
