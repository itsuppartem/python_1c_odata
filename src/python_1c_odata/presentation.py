"""1C presentation fields: ``Name____Presentation`` (four underscores)."""

from __future__ import annotations

from collections.abc import Sequence

PRESENTATION_SUFFIX = "____Presentation"
ALL_PRESENTATIONS = "*____Presentation"

SelectFields = str | Sequence[str]


def presentation(field: str) -> str:
    """``presentation("Контрагент")`` → ``Контрагент____Presentation``."""
    if field.endswith(PRESENTATION_SUFFIX):
        return field
    return f"{field}{PRESENTATION_SUFFIX}"


def join_select(select: SelectFields | None) -> str | None:
    if select is None:
        return None
    if isinstance(select, str):
        return select
    return ",".join(select)


def normalize_select(
    select: SelectFields | None,
    *,
    presentations: bool = False,
) -> str | None:
    """Join a list/tuple ``select`` and optionally append ``*____Presentation``."""
    text = join_select(select)
    if not presentations:
        return text
    parts = [] if not text else [part.strip() for part in text.split(",") if part.strip()]
    if ALL_PRESENTATIONS not in parts:
        parts.append(ALL_PRESENTATIONS)
    return ",".join(parts)
