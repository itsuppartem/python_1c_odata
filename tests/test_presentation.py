"""1C ____Presentation helpers and $select list / presentations=True."""

from urllib.parse import parse_qs, unquote

from python_1c_odata import ALL_PRESENTATIONS, Catalog, F, presentation


def test_presentation_uses_four_underscores():
    assert presentation("Контрагент") == "Контрагент____Presentation"
    assert presentation("Контрагент____Presentation") == "Контрагент____Presentation"
    assert ALL_PRESENTATIONS == "*____Presentation"


async def test_query_select_list_joins_with_comma(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await Catalog(infobase, "Товары").query(select=["Ref_Key", "Description"])
    qs = parse_qs(fake_odata.last["query"], keep_blank_values=True)
    assert qs["$select"] == ["Ref_Key,Description"]


async def test_query_presentations_appends_star_presentation(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await Catalog(infobase, "Товары").query(select="*", presentations=True)
    qs = parse_qs(fake_odata.last["query"], keep_blank_values=True)
    assert qs["$select"] == ["*,*____Presentation"]


async def test_query_presentations_only(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await Catalog(infobase, "Товары").query(presentations=True)
    qs = parse_qs(fake_odata.last["query"], keep_blank_values=True)
    assert qs["$select"] == ["*____Presentation"]


async def test_query_builder_select_list_and_presentations(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await (
        Catalog(infobase, "Товары")
        .where(F("DeletionMark").eq(False))
        .select(["Ref_Key", presentation("Контрагент")])
        .presentations()
        .execute()
    )
    qs = parse_qs(fake_odata.last["query"], keep_blank_values=True)
    assert qs["$select"] == ["Ref_Key,Контрагент____Presentation,*____Presentation"]


async def test_entity_set_url_builds_without_sending(fake_odata, infobase):
    url = Catalog(infobase, "Товары").url(
        top=5,
        select=["Ref_Key", "Description"],
        odata_filter=F("Цена") > 1,
        presentations=True,
    )
    assert "Catalog_Товары" in url
    assert "$top=5" in url
    assert "$select=Ref_Key,Description,*____Presentation" in url
    assert "Цена gt 1" in unquote(url)
    assert fake_odata.requests == []
