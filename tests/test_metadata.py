"""Lightweight $metadata EntitySet listing. Not codegen."""

from python_1c_odata.metadata import parse_entity_sets

_EDM = """<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx Version="1.0" xmlns:edmx="http://schemas.microsoft.com/ado/2007/06/edmx">
  <edmx:DataServices xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
      m:DataServiceVersion="3.0">
    <Schema Namespace="StandardODATA" xmlns="http://schemas.microsoft.com/ado/2009/11/edm">
      <EntityType Name="Catalog_Товары"/>
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
