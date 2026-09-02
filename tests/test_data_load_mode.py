"""1C_OData-DataLoadMode header on writes only."""

from python_1c_odata import Catalog, Document, Infobase, PostingMode

_KEY = "41aa6331-954f-11e3-814b-005056c00008"


async def test_writes_omit_header_by_default(fake_odata, infobase):
    fake_odata.respond(201, {"Ref_Key": _KEY})
    await Catalog(infobase, "Товары").create({"Description": "X"})
    assert fake_odata.last["data_load_mode"] == ""
    fake_odata.respond(200, {"Description": "Y"})
    await Catalog(infobase, "Товары").edit(_KEY, {"Description": "Y"})
    assert fake_odata.last["data_load_mode"] == ""
    fake_odata.respond(200, {"Description": "Z"})
    await Catalog(infobase, "Товары").replace(_KEY, {"Description": "Z"})
    assert fake_odata.last["data_load_mode"] == ""
    fake_odata.respond(204, b"")
    await Catalog(infobase, "Товары").delete(_KEY)
    assert fake_odata.last["data_load_mode"] == ""


async def test_query_never_sends_data_load_mode(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await Catalog(infobase, "Товары").query(top=1)
    assert fake_odata.last["method"] == "GET"
    assert fake_odata.last["data_load_mode"] == ""


async def test_per_call_data_load_mode_on_create_edit_replace_delete(fake_odata, infobase):
    fake_odata.respond(201, {"Ref_Key": _KEY})
    await Catalog(infobase, "Товары").create({"Description": "X"}, data_load_mode=True)
    assert fake_odata.last["data_load_mode"] == "true"
    fake_odata.respond(200, {"Description": "Y"})
    await Catalog(infobase, "Товары").edit(_KEY, {"Description": "Y"}, data_load_mode=True)
    assert fake_odata.last["data_load_mode"] == "true"
    fake_odata.respond(200, {"Description": "Z"})
    await Catalog(infobase, "Товары").replace(_KEY, {"Description": "Z"}, data_load_mode=True)
    assert fake_odata.last["data_load_mode"] == "true"
    fake_odata.respond(204, b"")
    await Catalog(infobase, "Товары").delete(_KEY, data_load_mode=True)
    assert fake_odata.last["data_load_mode"] == "true"


async def test_document_create_and_edit_per_call_header(fake_odata, infobase):
    fake_odata.respond(201, {"Ref_Key": _KEY})
    await Document(infobase, "Заказ").create(
        {"Date": "2024-01-01T00:00:00"},
        data_load_mode=True,
    )
    assert fake_odata.last["method"] == "POST"
    assert fake_odata.last["data_load_mode"] == "true"
    fake_odata.respond(200, {"Number": "1"})
    await Document(infobase, "Заказ").edit(_KEY, {"Number": "1"}, data_load_mode=True)
    assert fake_odata.last["data_load_mode"] == "true"


async def test_infobase_data_load_mode_applies_to_writes(fake_odata):
    ib = Infobase(fake_odata.base_url, "ut", "user", "secret", data_load_mode=True)
    fake_odata.respond(201, {"Ref_Key": _KEY})
    async with ib:
        await Catalog(ib, "Товары").create({"Description": "X"})
        assert fake_odata.last["data_load_mode"] == "true"
        fake_odata.respond(200, {"value": []})
        await Catalog(ib, "Товары").query(top=1)
        assert fake_odata.last["data_load_mode"] == ""
        fake_odata.respond(200, {"Description": "Y"})
        await Catalog(ib, "Товары").edit(_KEY, {"Description": "Y"}, data_load_mode=False)
        assert fake_odata.last["data_load_mode"] == ""


async def test_document_posting_uses_instance_flag(fake_odata):
    ib = Infobase(fake_odata.base_url, "ut", "user", "secret", data_load_mode=True)
    fake_odata.respond(201, {"Ref_Key": _KEY})
    async with ib:
        await Document(ib, "Заказ").create(
            {"Date": "2024-01-01T00:00:00"},
            posting_mode=PostingMode.POST,
        )
    assert fake_odata.requests[0]["data_load_mode"] == "true"
    assert fake_odata.requests[1]["path"].endswith("/Post")
    assert fake_odata.requests[1]["data_load_mode"] == "true"
