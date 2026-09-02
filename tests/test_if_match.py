"""If-Match / DataVersion on edit, replace, delete."""

from python_1c_odata import Catalog, Document

_KEY = "41aa6331-954f-11e3-814b-005056c00008"


async def test_edit_sends_if_match(fake_odata, infobase):
    fake_odata.respond(200, {"Description": "Новое"})
    await Catalog(infobase, "Товары").edit(_KEY, {"Description": "Новое"}, if_match="AAAAAAAAB9E=")
    assert fake_odata.last["method"] == "PATCH"
    assert fake_odata.last["if_match"] == "AAAAAAAAB9E="


async def test_replace_sends_if_match(fake_odata, infobase):
    fake_odata.respond(200, {"Description": "Полная"})
    await Catalog(infobase, "Товары").replace(_KEY, {"Description": "Полная"}, if_match="v2")
    assert fake_odata.last["method"] == "PUT"
    assert fake_odata.last["if_match"] == "v2"


async def test_delete_sends_if_match(fake_odata, infobase):
    fake_odata.respond(204, b"")
    await Catalog(infobase, "Товары").delete(_KEY, if_match="*")
    assert fake_odata.last["method"] == "DELETE"
    assert fake_odata.last["if_match"] == "*"


async def test_edit_omits_if_match_when_not_passed(fake_odata, infobase):
    fake_odata.respond(200, {"Description": "X"})
    await Catalog(infobase, "Товары").edit(_KEY, {"Description": "X"})
    assert fake_odata.last["if_match"] == ""


async def test_document_edit_forwards_if_match(fake_odata, infobase):
    fake_odata.respond(200, {"Number": "1"})
    await Document(infobase, "Заказ").edit(_KEY, {"Number": "1"}, if_match="dv")
    assert fake_odata.last["if_match"] == "dv"
    assert fake_odata.last["method"] == "PATCH"
