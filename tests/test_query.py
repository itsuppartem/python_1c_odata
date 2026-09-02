"""Page, iterate, count, and the Query builder against FakeOData."""

from urllib.parse import parse_qs

import pytest

from python_1c_odata import Catalog, F
from python_1c_odata.errors import ODataError
from python_1c_odata.page import Page


async def test_query_returns_page_and_accepts_filter_dsl(fake_odata, infobase):
    fake_odata.respond(200, {"value": [{"Description": "Сапоги"}], "__count": "1"})
    page = await Catalog(infobase, "Товары").query(
        odata_filter=F("Цена") > 1000,
        inlinecount=True,
    )
    assert isinstance(page, Page)
    assert page.value[0]["Description"] == "Сапоги"
    assert page.count == 1
    assert page["value"][0]["Description"] == "Сапоги"
    qs = parse_qs(fake_odata.last["query"], keep_blank_values=True)
    assert qs["$filter"] == ["Цена gt 1000"]
    assert qs["$inlinecount"] == ["allpages"]


async def test_query_builder_sends_readable_options(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    page = (
        await Catalog(infobase, "Товары")
        .where(F("DeletionMark").eq(False))
        .top(5)
        .select("Ref_Key")
        .execute()
    )
    assert page.value == []
    qs = parse_qs(fake_odata.last["query"], keep_blank_values=True)
    assert qs["$top"] == ["5"]
    assert qs["$select"] == ["Ref_Key"]
    assert qs["$filter"] == ["DeletionMark eq false"]


async def test_iterate_pages_with_top_skip_until_short_page(fake_odata, infobase):
    fake_odata.respond_sequence(
        (200, {"value": [{"i": 1}, {"i": 2}]}),
        (200, {"value": [{"i": 3}]}),
    )
    rows = [
        row
        async for row in Catalog(infobase, "Товары").iterate(
            page_size=2,
            odata_filter="DeletionMark eq false",
        )
    ]
    assert [row["i"] for row in rows] == [1, 2, 3]
    assert len(fake_odata.requests) == 2
    first = parse_qs(fake_odata.requests[0]["query"], keep_blank_values=True)
    second = parse_qs(fake_odata.requests[1]["query"], keep_blank_values=True)
    assert first["$top"] == ["2"]
    assert first["$skip"] == ["0"]
    assert first["$filter"] == ["DeletionMark eq false"]
    assert second["$skip"] == ["2"]


async def test_iterate_stops_on_empty_page(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    rows = [row async for row in Catalog(infobase, "Товары").iterate(page_size=10)]
    assert rows == []
    assert len(fake_odata.requests) == 1


async def test_count_uses_top0_inlinecount(fake_odata, infobase):
    fake_odata.respond(200, {"value": [], "__count": "42"})
    total = await Catalog(infobase, "Товары").count(odata_filter=F("Цена") > 1)
    assert total == 42
    qs = parse_qs(fake_odata.last["query"], keep_blank_values=True)
    assert qs["$top"] == ["0"]
    assert qs["$inlinecount"] == ["allpages"]
    assert qs["$filter"] == ["Цена gt 1"]


async def test_count_reads_odata_count_key(fake_odata, infobase):
    fake_odata.respond(200, {"value": [], "odata.count": "7"})
    assert await Catalog(infobase, "Товары").count() == 7


async def test_count_raises_when_server_omits_inlinecount(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    with pytest.raises(ODataError, match="inlinecount"):
        await Catalog(infobase, "Товары").count()


async def test_query_sends_any_filter_text(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await Catalog(infobase, "Заказы").query(odata_filter=F("Товары").any(F("Цена") > 10000))
    qs = parse_qs(fake_odata.last["query"], keep_blank_values=True)
    assert qs["$filter"] == ["Товары/any(d: d/Цена gt 10000)"]


async def test_builder_count_and_iterate(fake_odata, infobase):
    fake_odata.respond(200, {"value": [{"i": 1}], "__count": "1"})
    catalog = Catalog(infobase, "Товары")
    assert await catalog.build().where(F("Цена") > 1).count() == 1
    fake_odata.respond(200, {"value": [{"i": 1}]})
    rows = [row async for row in catalog.where(F("Цена") > 1).iterate(page_size=50)]
    assert rows == [{"i": 1}]
