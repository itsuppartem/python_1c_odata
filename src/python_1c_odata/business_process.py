from __future__ import annotations

from typing import Any

from python_1c_odata.entity import EntitySet


class BusinessProcess(EntitySet):
    kind = "BusinessProcess"

    async def start(
        self,
        key: str,
        *,
        route_point: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        extra = None if route_point is None else {"RoutePoint": route_point}
        return await self.infobase.post(
            self.entity,
            key=key,
            action="Start",
            extra=extra,
            timeout=timeout,
        )
