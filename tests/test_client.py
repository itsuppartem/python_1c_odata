"""HTTP client contract against a local OData stand-in."""

import json

import pytest

from python_1c_odata import Infobase
from python_1c_odata.errors import ODataError


async def test_get_returns_json_and_reuses_one_session(fake_odata, infobase):
    fake_odata.respond(200, {"value": [{"Ref_Key": "aaa"}]})
    first = await infobase.get("Catalog_Товары")
    session = infobase.session
    second = await infobase.get("Catalog_Товары")

    assert first == {"value": [{"Ref_Key": "aaa"}]}
    assert second == first
    assert infobase.session is session
    assert len(fake_odata.requests) == 2
    assert fake_odata.last["path"] == "/ut/odata/standard.odata/Catalog_Товары"
    assert "$format=json" in fake_odata.last["query"]
    assert fake_odata.last["authorization"].startswith("Basic ")


async def test_http_error_includes_1c_message(fake_odata, infobase):
    fake_odata.respond(
        400,
        {
            "odata.error": {
                "code": "9",
                "message": {"lang": "ru", "value": "Поле Date не заполнено"},
            }
        },
    )
    with pytest.raises(ODataError) as exc:
        await infobase.get("Document_Заказ")
    assert exc.value.status == 400
    assert "Поле Date не заполнено" in str(exc.value)


async def test_http_error_falls_back_to_raw_body(fake_odata, infobase):
    fake_odata.respond(500, "internal boom")
    with pytest.raises(ODataError) as exc:
        await infobase.get("Catalog_Товары")
    assert exc.value.status == 500
    assert "internal boom" in str(exc.value)


async def test_post_sends_json_and_accepts_201(fake_odata, infobase):
    fake_odata.respond(201, {"Ref_Key": "new"})
    result = await infobase.post("Catalog_Товары", json={"Description": "Сапоги"})
    assert result == {"Ref_Key": "new"}
    assert fake_odata.last["method"] == "POST"
    assert json.loads(fake_odata.last["body"]) == {"Description": "Сапоги"}
    assert "application/json" in fake_odata.last["content_type"]


async def test_aclose_does_not_close_injected_session(fake_odata):
    import aiohttp

    session = aiohttp.ClientSession()
    ib = Infobase(fake_odata.base_url, "ut", "u", "p", session=session)
    fake_odata.respond(200, {"value": []})
    await ib.get("Catalog_X")
    await ib.aclose()
    assert not session.closed
    await session.close()
