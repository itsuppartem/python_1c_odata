"""Documents: create/post/unpost rules from the 1C OData interface."""

import pytest

from python_1c_odata import Document, PostingMode
from python_1c_odata.errors import ODataError


async def test_create_rejects_posted_flag_before_http(fake_odata, infobase):
    with pytest.raises(ValueError, match="Posted"):
        await Document(infobase, "Заказ").create(
            {"Date": "2024-01-01T00:00:00", "Posted": True}
        )
    assert fake_odata.requests == []


async def test_create_requires_date(fake_odata, infobase):
    with pytest.raises(ValueError, match="Date"):
        await Document(infobase, "Заказ").create({"Number": "0001"})
    assert fake_odata.requests == []


async def test_create_unpost_only_hits_collection(fake_odata, infobase):
    fake_odata.respond(201, {"Ref_Key": "41aa6331-954f-11e3-814b-005056c00008"})
    created = await Document(infobase, "Заказ").create(
        {"Date": "2024-01-01T00:00:00"},
        posting_mode=PostingMode.UNPOST,
    )
    assert created["Ref_Key"].startswith("41aa")
    assert len(fake_odata.requests) == 1
    assert fake_odata.last["path"].endswith("Document_Заказ")


async def test_create_with_post_mode_posts_new_ref(fake_odata, infobase):
    fake_odata.respond(201, {"Ref_Key": "41aa6331-954f-11e3-814b-005056c00008"})
    await Document(infobase, "Заказ").create(
        {"Date": "2024-01-01T00:00:00"},
        posting_mode=PostingMode.POST,
    )
    assert len(fake_odata.requests) == 2
    assert fake_odata.last["path"].endswith(
        "Document_Заказ(guid'41aa6331-954f-11e3-814b-005056c00008')/Post"
    )
    assert "PostingModeOperational=false" in fake_odata.last["query"]


async def test_post_operational_sends_query_flag(fake_odata, infobase):
    fake_odata.respond(200, {})
    await Document(infobase, "Заказ").post(
        "41aa6331-954f-11e3-814b-005056c00008",
        PostingMode.OPER,
    )
    req = fake_odata.last
    assert req["method"] == "POST"
    assert req["path"].endswith(
        "Document_Заказ(guid'41aa6331-954f-11e3-814b-005056c00008')/Post"
    )
    assert "PostingModeOperational=true" in req["query"]


async def test_post_regular_sets_operational_false(fake_odata, infobase):
    fake_odata.respond(200, {})
    await Document(infobase, "Заказ").post(
        "41aa6331-954f-11e3-814b-005056c00008",
        PostingMode.POST,
    )
    assert "PostingModeOperational=false" in fake_odata.last["query"]


async def test_post_rejects_unpost_mode(fake_odata, infobase):
    with pytest.raises(ValueError, match="unpost"):
        await Document(infobase, "Заказ").post(
            "41aa6331-954f-11e3-814b-005056c00008",
            PostingMode.UNPOST,
        )
    assert fake_odata.requests == []


async def test_unpost_hits_unpost_action(fake_odata, infobase):
    fake_odata.respond(200, {})
    await Document(infobase, "Заказ").unpost("41aa6331-954f-11e3-814b-005056c00008")
    assert fake_odata.last["path"].endswith(
        "Document_Заказ(guid'41aa6331-954f-11e3-814b-005056c00008')/Unpost"
    )
    assert fake_odata.last["method"] == "POST"


async def test_edit_rejects_posted_field(fake_odata, infobase):
    with pytest.raises(ValueError, match="Posted"):
        await Document(infobase, "Заказ").edit(
            "41aa6331-954f-11e3-814b-005056c00008",
            {"Posted": False},
        )


async def test_post_http_error_is_odata_error(fake_odata, infobase):
    fake_odata.respond(400, {"odata.error": {"message": {"value": "уже проведён"}}})
    with pytest.raises(ODataError):
        await Document(infobase, "Заказ").post(
            "41aa6331-954f-11e3-814b-005056c00008",
            PostingMode.POST,
        )
