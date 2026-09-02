"""Build 1C standard OData 3.0 URLs without letting a generic HTTP client rewrite them."""

from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import quote

from python_1c_odata.literals import guid

_ODATA_QUERY_SAFE = "$,'()/:;_!=*"


def infobase_root(server: str, infobase: str) -> str:
    return f"{server.rstrip('/')}/{infobase.strip('/')}/odata/standard.odata"


def entity_path(root: str, entity: str) -> str:
    return f"{root.rstrip('/')}/{entity}"


def key_path(root: str, entity: str, key: str | Mapping[str, str]) -> str:
    base = entity_path(root, entity)
    if isinstance(key, Mapping):
        inner = ",".join(f"{name}={_key_literal(value)}" for name, value in key.items())
        return f"{base}({inner})"
    return f"{base}({guid(key)})"


def query_string(
    *,
    top: int | None = None,
    skip: int | None = None,
    select: str | None = None,
    odata_filter: str | None = None,
    expand: str | None = None,
    orderby: str | None = None,
    extra: Mapping[str, str] | None = None,
    allowed_only: bool = False,
    inlinecount: bool = False,
) -> str:
    if top is not None and type(top) is not int:
        raise TypeError(f"top={top!r} must be int")
    if skip is not None and type(skip) is not int:
        raise TypeError(f"skip={skip!r} must be int")

    parts: list[str] = ["$format=json"]
    if top is not None:
        parts.append(f"$top={top}")
    if skip is not None:
        parts.append(f"$skip={skip}")
    if select is not None:
        parts.append(f"$select={_enc(select)}")
    if odata_filter is not None:
        parts.append(f"$filter={_enc(odata_filter)}")
    if expand is not None:
        parts.append(f"$expand={_enc(expand)}")
    if orderby is not None:
        parts.append(f"$orderby={_enc(orderby)}")
    if extra:
        for name, value in extra.items():
            parts.append(f"{name}={_enc(value)}")
    if allowed_only:
        parts.append("allowedOnly=true")
    if inlinecount:
        parts.append("$inlinecount=allpages")
    return "?" + "&".join(parts)


def _key_literal(value: str) -> str:
    text = str(value)
    if text.startswith(("guid'", "datetime'")) or (text.startswith("'") and text.endswith("'")):
        return text
    try:
        return guid(text)
    except ValueError:
        return "'" + text.replace("'", "''") + "'"


def slice_path(
    root: str,
    entity: str,
    function: str,
    *,
    period: str | None = None,
    condition: str | None = None,
) -> str:
    args = _named_args(Period=period, Condition=_quoted_condition(condition))
    return f"{entity_path(root, entity)}/{function}({args})"


def accumulation_virtual_path(
    root: str,
    entity: str,
    function: str,
    *,
    period: str | None = None,
    start_period: str | None = None,
    end_period: str | None = None,
    condition: str | None = None,
) -> str:
    args = _named_args(
        Period=period,
        StartPeriod=start_period,
        EndPeriod=end_period,
        Condition=_quoted_condition(condition),
    )
    return f"{entity_path(root, entity)}/{function}({args})"


def calculation_virtual_path(
    root: str,
    entity: str,
    function: str,
    *,
    condition: str | None = None,
) -> str:
    """Calculation register virtual table. 1C OData: ScheduledData, ActualActionPeriod."""
    return accumulation_virtual_path(root, entity, function, condition=condition)


def _quoted_condition(condition: str | None) -> str | None:
    if condition is None:
        return None
    return f"'{condition}'"


def _named_args(**kwargs: str | None) -> str:
    return ",".join(f"{name}={value}" for name, value in kwargs.items() if value is not None)


def _enc(value: str) -> str:
    return quote(value, safe=_ODATA_QUERY_SAFE)
