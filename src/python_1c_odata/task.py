from __future__ import annotations

from typing import Any

from python_1c_odata.entity import EntitySet


class Task(EntitySet):
    kind = "Task"

    async def execute(self, key: str, *, timeout: float | None = None) -> Any:
        return await self.infobase.post(
            self.entity, key=key, action="ExecuteTask", timeout=timeout
        )
