"""HTTP status mapping to typed ODataError subclasses."""

import pytest

from python_1c_odata import AccessDenied, Catalog, ConcurrencyError, EntityNotFound, ODataError


async def test_404_is_entity_not_found(fake_odata, infobase):
    fake_odata.respond(404, {"odata.error": {"message": {"value": "не найден"}}})
    with pytest.raises(EntityNotFound) as exc:
        await Catalog(infobase, "Товары").get("41aa6331-954f-11e3-814b-005056c00008")
    assert isinstance(exc.value, ODataError)
    assert exc.value.status == 404
    assert "не найден" in str(exc.value)


async def test_403_is_access_denied(fake_odata, infobase):
    fake_odata.respond(403, {"odata.error": {"message": {"value": "нет прав"}}})
    with pytest.raises(AccessDenied) as exc:
        await Catalog(infobase, "Товары").query()
    assert exc.value.status == 403


async def test_412_is_concurrency_error(fake_odata, infobase):
    fake_odata.respond(412, {"odata.error": {"message": {"value": "DataVersion"}}})
    with pytest.raises(ConcurrencyError) as exc:
        await Catalog(infobase, "Товары").edit(
            "41aa6331-954f-11e3-814b-005056c00008",
            {"Description": "X"},
            if_match="stale",
        )
    assert exc.value.status == 412
    assert isinstance(exc.value, ODataError)


async def test_odata_error_parses_internal_code(fake_odata, infobase):
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
        await Catalog(infobase, "Товары").create({"Description": "X"})
    assert exc.value.status == 400
    assert exc.value.internal_code == "9"
    assert "Поле Date не заполнено" in str(exc.value)
    assert exc.value.__class__ is ODataError


async def test_typed_404_keeps_internal_code(fake_odata, infobase):
    fake_odata.respond(404, {"error": {"code": 0, "message": "missing"}})
    with pytest.raises(EntityNotFound) as exc:
        await Catalog(infobase, "Товары").get("41aa6331-954f-11e3-814b-005056c00008")
    assert exc.value.internal_code == "0"


async def test_atom_error_fills_internal_code(fake_odata, infobase):
    fake_odata.respond(
        400,
        """<?xml version="1.0"?>
<m:error xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
  <m:code>9</m:code>
  <m:message>Поле Date не заполнено</m:message>
</m:error>""",
    )
    with pytest.raises(ODataError) as exc:
        await Catalog(infobase, "Товары").create({"Description": "X"})
    assert exc.value.internal_code == "9"
    assert "Поле Date не заполнено" in str(exc.value)
