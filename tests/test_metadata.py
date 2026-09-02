"""Lightweight $metadata EntitySet / EntityType listing. Not codegen."""

import pytest

from python_1c_odata.metadata import parse_entity_sets, parse_metadata

_EDM = """<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx Version="1.0" xmlns:edmx="http://schemas.microsoft.com/ado/2007/06/edmx">
  <edmx:DataServices xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
      m:DataServiceVersion="3.0">
    <Schema Namespace="StandardODATA" xmlns="http://schemas.microsoft.com/ado/2009/11/edm">
      <EntityType Name="Catalog_Товары">
        <Key>
          <PropertyRef Name="Ref_Key"/>
        </Key>
        <Property Name="Ref_Key" Type="Edm.Guid" Nullable="false"/>
        <Property Name="Description" Type="Edm.String" Nullable="true"/>
        <Property Name="Артикул" Type="Edm.String"/>
        <NavigationProperty Name="Владелец"/>
      </EntityType>
      <EntityType Name="AccumulationRegister_ТоварыНаСкладах"/>
      <EntityContainer Name="StandardODATA">
        <EntitySet Name="Catalog_Товары" EntityType="StandardODATA.Catalog_Товары"/>
        <EntitySet Name="AccumulationRegister_ТоварыНаСкладах"
            EntityType="StandardODATA.AccumulationRegister_ТоварыНаСкладах"/>
        <FunctionImport Name="Balance"/>
      </EntityContainer>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>
"""


def test_parse_entity_sets_reads_cyrillic_and_skips_function_import():
    sets = parse_entity_sets(_EDM)
    assert [item.name for item in sets] == [
        "Catalog_Товары",
        "AccumulationRegister_ТоварыНаСкладах",
    ]
    assert sets[0].entity_type == "StandardODATA.Catalog_Товары"
    assert sets[1].entity_type == "StandardODATA.AccumulationRegister_ТоварыНаСкладах"


def test_parse_entity_type_keys_properties_and_navigation():
    model = parse_metadata(_EDM)
    info = model.entity_type_for_set("Catalog_Товары")
    assert info is not None
    assert info.name == "Catalog_Товары"
    assert info.keys == ("Ref_Key",)
    names = [prop.name for prop in info.properties]
    assert names == ["Ref_Key", "Description", "Артикул"]
    by_name = {prop.name: prop for prop in info.properties}
    assert by_name["Ref_Key"].type == "Edm.Guid"
    assert by_name["Ref_Key"].nullable is False
    assert by_name["Description"].nullable is True
    assert by_name["Артикул"].nullable is None
    assert info.navigation_properties == ("Владелец",)


async def test_entity_sets_fetches_once_and_has_entity_set(fake_odata, infobase):
    fake_odata.respond(200, _EDM)
    names = await infobase.entity_sets()
    assert names == ["Catalog_Товары", "AccumulationRegister_ТоварыНаСкладах"]
    assert await infobase.has_entity_set("Catalog_Товары")
    assert not await infobase.has_entity_set("Catalog_НетТакого")
    again = await infobase.entity_sets()
    assert again == names
    metadata_hits = [req for req in fake_odata.requests if req["path"].endswith("/$metadata")]
    assert len(metadata_hits) == 1
    assert "$format=json" not in metadata_hits[0]["query"]


async def test_entity_type_for_set_uses_cached_model(fake_odata, infobase):
    fake_odata.respond(200, _EDM)
    info = await infobase.entity_type_for_set("Catalog_Товары")
    assert info.keys == ("Ref_Key",)
    assert [prop.name for prop in info.properties] == ["Ref_Key", "Description", "Артикул"]
    again = await infobase.entity_type_for_set("Catalog_Товары")
    assert again == info
    assert len([req for req in fake_odata.requests if req["path"].endswith("/$metadata")]) == 1
    with pytest.raises(KeyError):
        await infobase.entity_type_for_set("Catalog_НетТакого")
