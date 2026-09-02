"""1C write helpers: ``@odata.bind`` links and ValueStorage ``_Base64Data`` fields."""

from __future__ import annotations

from collections.abc import Mapping

from python_1c_odata.url import entity_key

_BASE64_SUFFIX = "_Base64Data"


def odata_bind(entity_set: str, guid_or_key: str | Mapping[str, str]) -> str:
    """``odata_bind("Catalog_Организации", guid)`` → ``Catalog_Организации(guid'...')``."""
    return entity_key(entity_set, guid_or_key)


def base64_data(field: str) -> str:
    """``base64_data("Файл")`` → ``Файл_Base64Data`` (1C ValueStorage write field)."""
    if field.endswith(_BASE64_SUFFIX):
        return field
    return f"{field}{_BASE64_SUFFIX}"


def bind_field(
    name: str,
    entity_set: str,
    key: str | Mapping[str, str],
) -> dict[str, str]:
    """``{"Организация@odata.bind": "Catalog_Организации(guid'...')"}``."""
    return {f"{name}@odata.bind": odata_bind(entity_set, key)}
