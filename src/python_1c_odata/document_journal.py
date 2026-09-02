from __future__ import annotations

from python_1c_odata.entity import ReadOnlyEntitySet


class DocumentJournal(ReadOnlyEntitySet):
    """1C document journal. Standard OData exposes query/get only."""

    kind = "DocumentJournal"
