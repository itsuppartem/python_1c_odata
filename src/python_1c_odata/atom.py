"""OData 3.0 Atom/XML ↔ the same dicts the JSON client already uses.

stdlib ``xml.etree`` only. Namespace-tolerant (local tag names).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from xml.etree import ElementTree
from xml.sax.saxutils import escape

ATOM_NS = "http://www.w3.org/2005/Atom"
D_NS = "http://schemas.microsoft.com/ado/2007/08/dataservices"
M_NS = "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"

_ATOM_MARKERS = ("<?xml", "<feed", "<entry", "<m:error")


def looks_like_atom(text: str) -> bool:
    head = text.lstrip("\ufeff \t\r\n")[:500].lower()
    return any(marker in head for marker in _ATOM_MARKERS)


def looks_like_xml_content_type(content_type: str) -> bool:
    lowered = content_type.lower()
    return (
        "atom+xml" in lowered
        or "application/xml" in lowered
        or lowered.startswith("text/xml")
        or "text/xml;" in lowered
    )


def decode_atom(text: str) -> Any:
    """``<feed>`` → ``{"value": [...]}``; ``<entry>`` → entity dict."""
    root = ElementTree.fromstring(text)
    local = _local_name(root.tag)
    if local == "feed":
        return _decode_feed(root)
    if local == "entry":
        return _decode_entry(root)
    for child in root:
        child_local = _local_name(child.tag)
        if child_local == "feed":
            return _decode_feed(child)
        if child_local == "entry":
            return _decode_entry(child)
    raise ValueError(f"unsupported Atom root <{local}>")


def parse_atom_error(text: str) -> tuple[str | None, str] | None:
    """``<m:error>`` → ``(code, message)``, or ``None`` if this is not Atom error XML."""
    if not text or not looks_like_atom(text):
        return None
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError:
        return None
    error_el = root if _local_name(root.tag) == "error" else None
    if error_el is None:
        for el in root.iter():
            if _local_name(el.tag) == "error":
                error_el = el
                break
    if error_el is None:
        return None
    code: str | None = None
    message = ""
    for child in error_el:
        local = _local_name(child.tag)
        if local == "code":
            raw = (child.text or "").strip()
            code = raw or None
        elif local == "message":
            message = (child.text or "").strip()
    return code, message or text


def encode_entry(data: Mapping[str, Any]) -> str:
    """Python create/edit dict → Atom ``<entry>``. Skips ``@odata.bind`` keys."""
    props: list[str] = []
    for key, value in data.items():
        if key.endswith("@odata.bind"):
            continue
        if isinstance(value, (dict, list)):
            continue
        props.append(_property_xml(key, value))
    inner = "".join(props)
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<entry xmlns="{ATOM_NS}" xmlns:d="{D_NS}" xmlns:m="{M_NS}">'
        f'<content type="application/xml"><m:properties>{inner}</m:properties></content>'
        "</entry>"
    )


def _decode_feed(feed: ElementTree.Element) -> dict[str, Any]:
    values: list[dict[str, Any]] = []
    count: str | None = None
    for child in feed:
        local = _local_name(child.tag)
        if local == "entry":
            values.append(_decode_entry(child))
        elif local == "count":
            raw = (child.text or "").strip()
            count = raw or None
    payload: dict[str, Any] = {"value": values}
    if count is not None:
        payload["odata.count"] = count
    return payload


def _decode_entry(entry: ElementTree.Element) -> dict[str, Any]:
    for el in entry.iter():
        if _local_name(el.tag) == "properties":
            return _decode_properties(el)
    return {}


def _decode_properties(props: ElementTree.Element) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for child in props:
        name = _local_name(child.tag)
        if _attr_local(child, "null") == "true":
            result[name] = None
            continue
        nested = [c for c in child if _local_name(c.tag) == "properties"]
        if nested:
            result[name] = _decode_properties(nested[0])
            continue
        result[name] = _coerce_value(_attr_local(child, "type"), (child.text or "").strip())
    return result


def _coerce_value(edm_type: str | None, text: str) -> Any:
    if not edm_type:
        return text
    kind = edm_type.rsplit(".", 1)[-1].lower()
    if kind == "boolean":
        return text.lower() == "true"
    if kind in {"int16", "int32", "int64", "byte", "sbyte"}:
        try:
            return int(text)
        except ValueError:
            return text
    if kind in {"double", "single"}:
        try:
            return float(text)
        except ValueError:
            return text
    return text


def _property_xml(name: str, value: Any) -> str:
    if value is None:
        return f'<d:{name} m:null="true" />'
    if isinstance(value, bool):
        text = "true" if value else "false"
        return f'<d:{name} m:type="Edm.Boolean">{text}</d:{name}>'
    if isinstance(value, int):
        return f'<d:{name} m:type="Edm.Int64">{value}</d:{name}>'
    if isinstance(value, float):
        return f'<d:{name} m:type="Edm.Double">{value}</d:{name}>'
    return f"<d:{name}>{escape(str(value))}</d:{name}>"


def _attr_local(el: ElementTree.Element, name: str) -> str | None:
    for key, value in el.attrib.items():
        if _local_name(key) == name:
            return value
    return None


def _local_name(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag.rsplit("}", 1)[-1]
    if ":" in tag:
        return tag.rsplit(":", 1)[-1]
    return tag
