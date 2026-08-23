"""Catalog CRUD. Fails if the client hits the wrong entity or swallows HTTP errors."""

import json
from urllib.parse import parse_qs

import pytest

from python_1c_odata import Catalog
from python_1c_odata.errors import ODataError


async def test_query_hits_catalog_collection_with_odata_options(fake_odata, infobase):
    fake_odata.respond(200, {"value": [{"Description": "Сапоги"}]})
    catalog = Catalog(infobase, "Товары")
    payload = await catalog.query(
        top=10,
        skip=2,
        select="Ref_Key,Description",
        odata_filter="DeletionMark eq false",
        expand="Владелец",
        orderby="Description",
    )
    assert payload["value"][0]["Description"] == "Сапоги"
    req = fake_odata.last
    qs = parse_qs(req["query"], keep_blank_values=True)
    assert req["method"] == "GET"
    assert req["path"] == "/ut/odata/standard.odata/Catalog_Товары"
    assert qs["$top"] == ["10"]
    assert qs["$skip"] == ["2"]
    assert qs["$select"] == ["Ref_Key,Description"]
    assert qs["$filter"] == ["DeletionMark eq false"]
    assert qs["$expand"] == ["Владелец"]
    assert qs["$orderby"] == ["Description"]


async def test_get_uses_guid_key(fake_odata, infobase):
    fake_odata.respond(200, {"Description": "Сапоги"})
    item = await Catalog(infobase, "Товары").get("41aa6331-954f-11e3-814b-005056c00008")
    assert item["Description"] == "Сапоги"
    assert fake_odata.last["path"].endswith(
        "Catalog_Товары(guid'41aa6331-954f-11e3-814b-005056c00008')"
    )


async def test_create_posts_json_and_returns_entity(fake_odata, infobase):
    fake_odata.respond(201, {"Ref_Key": "abc", "Description": "Сапоги"})
    created = await Catalog(infobase, "Товары").create({"Description": "Сапоги"})
    assert created["Ref_Key"] == "abc"
    assert fake_odata.last["method"] == "POST"
    assert json.loads(fake_odata.last["body"]) == {"Description": "Сапоги"}


async def test_create_raises_on_http_error_instead_of_printing(fake_odata, infobase, capsys):
    fake_odata.respond(400, {"odata.error": {"message": {"value": "дубль кода"}}})
    with pytest.raises(ODataError):
        await Catalog(infobase, "Товары").create({"Description": "X"})
    assert capsys.readouterr().out == ""


async def test_edit_patches_entity(fake_odata, infobase):
    fake_odata.respond(200, {"Description": "Новое"})
    await Catalog(infobase, "Товары").edit(
        "41aa6331-954f-11e3-814b-005056c00008",
        {"Description": "Новое"},
    )
    assert fake_odata.last["method"] == "PATCH"
    assert fake_odata.last["path"].endswith(
        "Catalog_Товары(guid'41aa6331-954f-11e3-814b-005056c00008')"
    )


async def test_delete_uses_http_delete(fake_odata, infobase):
    fake_odata.respond(204, b"")
    await Catalog(infobase, "Товары").delete("41aa6331-954f-11e3-814b-005056c00008")
    assert fake_odata.last["method"] == "DELETE"


async def test_replace_uses_put(fake_odata, infobase):
    fake_odata.respond(200, {"Description": "Полная"})
    await Catalog(infobase, "Товары").replace(
        "41aa6331-954f-11e3-814b-005056c00008",
        {"Description": "Полная"},
    )
    assert fake_odata.last["method"] == "PUT"
