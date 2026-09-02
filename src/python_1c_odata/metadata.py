"""Parse 1C $metadata CSDL/EDM for EntitySet names. Not a codegen."""

from __future__ import annotations

from dataclasses import dataclass
from xml.etree import ElementTree


@dataclass(frozen=True)
class EntitySetInfo:
    name: str
    entity_type: str | None = None


def parse_entity_sets(xml: str) -> list[EntitySetInfo]:
    root = ElementTree.fromstring(xml)
    found: list[EntitySetInfo] = []
    seen: set[str] = set()
    for el in root.iter():
        if _local_name(el.tag) != "EntitySet":
            continue
        name = el.attrib.get("Name")
        if not name or name in seen:
            continue
        seen.add(name)
        found.append(EntitySetInfo(name=name, entity_type=el.attrib.get("EntityType")))
    return found


def _local_name(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag
