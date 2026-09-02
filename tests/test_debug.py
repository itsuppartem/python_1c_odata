"""Infobase debug: readable URL, timing, no Authorization leak."""

import logging

import pytest

from python_1c_odata import Catalog, EntityNotFound, Infobase


async def test_debug_callable_redacts_authorization(fake_odata):
    lines: list[str] = []
    ib = Infobase(fake_odata.base_url, "ut", "user", "secret", debug=lines.append)
    fake_odata.respond(200, {"value": []})
    async with ib:
        await Catalog(ib, "Товары").query(odata_filter="Цена gt 1000")
    assert len(lines) == 1
    line = lines[0]
    assert line.startswith("GET ")
    assert " 200 " in line
    assert line.endswith("ms")
    assert "Authorization" not in line
    assert "secret" not in line
    assert fake_odata.last["authorization"] not in line
    assert "Цена gt 1000" in line
    assert "%D0" not in line


async def test_debug_true_uses_logger(fake_odata, caplog):
    ib = Infobase(fake_odata.base_url, "ut", "user", "secret", debug=True)
    fake_odata.respond(200, {"value": []})
    with caplog.at_level(logging.INFO, logger="python_1c_odata"):
        async with ib:
            await ib.get("Catalog_Товары")
    assert any("GET " in rec.message and "200" in rec.message for rec in caplog.records)
    assert all("secret" not in rec.message for rec in caplog.records)


async def test_last_url_and_status_on_success_and_error(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await Catalog(infobase, "Товары").query(top=1)
    assert infobase.last_status == 200
    assert infobase.last_url is not None
    assert "Catalog_Товары" in infobase.last_url
    assert "$top=1" in infobase.last_url

    fake_odata.respond(404, {"odata.error": {"message": {"value": "нет"}}})
    with pytest.raises(EntityNotFound):
        await Catalog(infobase, "НетТакого").get("41aa6331-954f-11e3-814b-005056c00008")
    assert infobase.last_status == 404
    assert infobase.last_url is not None
    assert "НетТакого" in infobase.last_url
