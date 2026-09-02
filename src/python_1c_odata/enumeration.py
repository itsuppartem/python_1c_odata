from __future__ import annotations

from python_1c_odata.entity import ReadOnlyEntitySet


class Enumeration(ReadOnlyEntitySet):
    """1C enumeration (Перечисление). Standard OData exposes query/get only."""

    kind = "Enumeration"
