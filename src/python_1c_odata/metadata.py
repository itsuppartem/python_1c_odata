"""Parse 1C $metadata CSDL/EDM. Not a codegen."""

from __future__ import annotations

from dataclasses import dataclass
from xml.etree import ElementTree


@dataclass(frozen=True)
class EntitySetInfo:
    name: str
    entity_type: str | None = None


@dataclass(frozen=True)
class PropertyInfo:
    name: str
    type: str | None = None
    nullable: bool | None = None


@dataclass(frozen=True)
class EntityTypeInfo:
    name: str
    keys: tuple[str, ...] = ()
    properties: tuple[PropertyInfo, ...] = ()
    navigation_properties: tuple[str, ...] = ()


@dataclass(frozen=True)
class MetadataModel:
    entity_sets: tuple[EntitySetInfo, ...]
    entity_types: tuple[EntityTypeInfo, ...]

    def entity_set(self, name: str) -> EntitySetInfo | None:
        for item in self.entity_sets:
            if item.name == name:
                return item
        return None

    def entity_type(self, name: str) -> EntityTypeInfo | None:
        short = name.rsplit(".", 1)[-1]
        for item in self.entity_types:
            if item.name == name or item.name == short:
                return item
        return None

    def entity_type_for_set(self, name: str) -> EntityTypeInfo | None:
        info = self.entity_set(name)
        if info is None:
            return None
        return self.entity_type(info.entity_type or name)


def parse_entity_sets(xml: str) -> list[EntitySetInfo]:
    return list(parse_metadata(xml).entity_sets)


def parse_metadata(xml: str) -> MetadataModel:
    root = ElementTree.fromstring(xml)
    sets: list[EntitySetInfo] = []
    types: list[EntityTypeInfo] = []
    seen_sets: set[str] = set()
    seen_types: set[str] = set()
    for el in root.iter():
        local = _local_name(el.tag)
        if local == "EntitySet":
            name = el.attrib.get("Name")
            if not name or name in seen_sets:
                continue
            seen_sets.add(name)
            sets.append(EntitySetInfo(name=name, entity_type=el.attrib.get("EntityType")))
        elif local == "EntityType":
            name = el.attrib.get("Name")
            if not name or name in seen_types:
                continue
            seen_types.add(name)
            types.append(_parse_entity_type(el, name))
    return MetadataModel(entity_sets=tuple(sets), entity_types=tuple(types))


def _parse_entity_type(el: ElementTree.Element, name: str) -> EntityTypeInfo:
    keys: list[str] = []
    props: list[PropertyInfo] = []
    navs: list[str] = []
    for child in el.iter():
        local = _local_name(child.tag)
        if local == "PropertyRef":
            ref = child.attrib.get("Name")
            if ref:
                keys.append(ref)
        elif local == "Property" and child is not el:
            pname = child.attrib.get("Name")
            if pname:
                props.append(
                    PropertyInfo(
                        name=pname,
                        type=child.attrib.get("Type"),
                        nullable=_parse_nullable(child.attrib.get("Nullable")),
                    )
                )
        elif local == "NavigationProperty":
            nname = child.attrib.get("Name")
            if nname:
                navs.append(nname)
    return EntityTypeInfo(
        name=name,
        keys=tuple(keys),
        properties=tuple(props),
        navigation_properties=tuple(navs),
    )


def _parse_nullable(raw: str | None) -> bool | None:
    if raw is None:
        return None
    return raw.lower() == "true"


def _local_name(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag
