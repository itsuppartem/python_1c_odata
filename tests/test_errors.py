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
