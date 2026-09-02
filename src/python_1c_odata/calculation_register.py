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

    async def recalculation(
        self,
        condition: str | Filter | None = None,
        *,
        select: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        return await self._virtual(
            "Recalculation",
            condition=condition,
            select=select,
            timeout=timeout,
        )

    async def base(
        self,
        condition: str | Filter | None = None,
        *,
        main_register_dimensions: str | None = None,
        base_register_dimensions: str | None = None,
        view_points: str | None = None,
        select: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        return await self._virtual(
            "Base",
            condition=condition,
            main_register_dimensions=main_register_dimensions,
            base_register_dimensions=base_register_dimensions,
            view_points=view_points,
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
        main_register_dimensions: str | None = None,
        base_register_dimensions: str | None = None,
        view_points: str | None = None,
    ) -> Any:
        path = calculation_virtual_path(
            self.infobase.root,
            self.entity,
            function,
            condition=None if condition is None else str(condition),
            main_register_dimensions=main_register_dimensions,
            base_register_dimensions=base_register_dimensions,
            view_points=view_points,
        )
        url = path + query_string(select=select)
        return await self.infobase.request("GET", url, timeout=timeout)
