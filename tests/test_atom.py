"""Atom/XML codec and Infobase format=atom / format=auto against FakeOData."""

from xml.etree import ElementTree

import pytest

from python_1c_odata import Catalog, Infobase, InformationRegister, ODataError
from python_1c_odata.atom import decode_atom, encode_entry, parse_atom_error
from python_1c_odata.page import Page

_GUID = "41aa6331-954f-11e3-814b-005056c00008"

ATOM_FEED = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
      xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
  <title type="text">Catalog_Goods</title>
  <m:count>2</m:count>
  <entry>
    <content type="application/xml">
      <m:properties>
        <d:Ref_Key m:type="Edm.Guid">{_GUID}</d:Ref_Key>
        <d:Description>Сапоги</d:Description>
        <d:DeletionMark m:type="Edm.Boolean">false</d:DeletionMark>
        <d:Количество m:type="Edm.Int32">3</d:Количество>
        <d:Цена m:type="Edm.Decimal">100.50</d:Цена>
        <d:Comment m:null="true" />
        <d:Наименование>Сапоги кожаные</d:Наименование>
      </m:properties>
    </content>
  </entry>
</feed>
"""

ATOM_ENTRY = f"""<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom"
       xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
       xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
  <content type="application/xml">
    <m:properties>
      <d:Ref_Key m:type="Edm.Guid">{_GUID}</d:Ref_Key>
      <d:Description>Сапоги</d:Description>
      <d:Артикул>A-1</d:Артикул>
    </m:properties>
  </content>
</entry>
"""

ATOM_ERROR = """<?xml version="1.0" encoding="utf-8"?>
<m:error xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata">
  <m:code>9</m:code>
  <m:message xml:lang="ru">Поле Date не заполнено</m:message>
</m:error>
"""


def test_decode_feed_value_count_null_and_types():
    payload = decode_atom(ATOM_FEED)
    row = payload["value"][0]
    assert row["Ref_Key"] == _GUID
    assert row["Description"] == "Сапоги"
    assert row["DeletionMark"] is False
    assert row["Количество"] == 3
    assert row["Цена"] == "100.50"
    assert row["Comment"] is None
    assert row["Наименование"] == "Сапоги кожаные"
    assert payload["odata.count"] == "2"


def test_decode_single_entry():
    entity = decode_atom(ATOM_ENTRY)
    assert entity["Ref_Key"] == _GUID
    assert entity["Артикул"] == "A-1"


def test_parse_atom_error_code_and_message():
    code, message = parse_atom_error(ATOM_ERROR) or (None, "")
    assert code == "9"
    assert message == "Поле Date не заполнено"


def test_encode_entry_skips_bind_and_writes_properties():
    xml = encode_entry(
        {
            "Description": "Сапоги",
            "Ref_Key": _GUID,
            "Артикул": "A-1",
            "Организация@odata.bind": "Catalog_Организации(guid'aaa')",
            "DeletionMark": False,
        }
    )
    assert "@odata.bind" not in xml
    root = ElementTree.fromstring(xml)
    texts = {el.tag.rsplit("}", 1)[-1]: (el.text or "") for el in root.iter() if el.text}
    assert texts["Description"] == "Сапоги"
    assert texts["Ref_Key"] == _GUID
    assert texts["Артикул"] == "A-1"
    assert texts["DeletionMark"] == "false"


def test_infobase_rejects_unknown_format():
    with pytest.raises(ValueError, match="atom"):
        Infobase("http://h", "ut", "u", "p", format="odata4")


async def test_atom_query_feed_to_page(fake_odata, atom_infobase):
    fake_odata.respond(200, ATOM_FEED, content_type="application/atom+xml")
    page = await Catalog(atom_infobase, "Goods").query(top=10)
    assert isinstance(page, Page)
    assert page.value[0]["Ref_Key"] == _GUID
    assert page.count == 2
    req = fake_odata.last
    assert "$format=atom" in req["query"]
    assert "$format=json" not in req["query"]
    assert "atom+xml" in req["accept"]


async def test_atom_get_and_create_entry(fake_odata, atom_infobase):
    fake_odata.respond(200, ATOM_ENTRY, content_type="application/atom+xml")
    item = await Catalog(atom_infobase, "Goods").get(_GUID)
    assert item["Ref_Key"] == _GUID
    assert item["Description"] == "Сапоги"

    fake_odata.respond(201, ATOM_ENTRY, content_type="application/atom+xml")
    created = await Catalog(atom_infobase, "Goods").create(
        {"Description": "Сапоги", "Артикул": "A-1", "Организация@odata.bind": "Catalog_X(guid'aaa')"}
    )
    assert created["Ref_Key"] == _GUID
    req = fake_odata.last
    assert req["method"] == "POST"
    assert "$format=atom" in req["query"]
    assert "atom+xml" in req["accept"]
    assert "atom+xml" in req["content_type"]
    assert req["data_service_version"] == "3.0"
    assert req["max_data_service_version"] == "3.0"
    body = req["body"].decode()
    assert "<entry" in body
    assert "Description" in body
    assert "Артикул" in body
    assert "Сапоги" in body
    assert "@odata.bind" not in body


async def test_atom_edit_sends_entry(fake_odata, atom_infobase):
    fake_odata.respond(200, ATOM_ENTRY, content_type="application/atom+xml")
    await Catalog(atom_infobase, "Goods").edit(_GUID, {"Description": "Новое"})
    req = fake_odata.last
    assert req["method"] == "PATCH"
    assert "<entry" in req["body"].decode()
    assert "Новое" in req["body"].decode()
    assert req["data_service_version"] == "3.0"


async def test_atom_m_error_is_odata_error(fake_odata, atom_infobase):
    fake_odata.respond(400, ATOM_ERROR, content_type="application/atom+xml")
    with pytest.raises(ODataError) as exc:
        await Catalog(atom_infobase, "Goods").create({"Description": "X"})
    assert exc.value.status == 400
    assert exc.value.internal_code == "9"
    assert "Поле Date не заполнено" in str(exc.value)


async def test_auto_parses_atom_despite_format_json(fake_odata, auto_infobase):
    fake_odata.respond(200, ATOM_FEED, content_type="application/atom+xml")
    page = await Catalog(auto_infobase, "Goods").query(top=5)
    assert page.value[0]["Ref_Key"] == _GUID
    assert "$format=json" in fake_odata.last["query"]
    assert "application/json" in fake_odata.last["accept"]


async def test_auto_parses_atom_when_content_type_lies(fake_odata, auto_infobase):
    fake_odata.respond(200, ATOM_FEED)
    page = await Catalog(auto_infobase, "Goods").query()
    assert page.value[0]["Наименование"] == "Сапоги кожаные"
    assert "$format=json" in fake_odata.last["query"]


async def test_json_default_still_sends_json(fake_odata, infobase):
    fake_odata.respond(200, {"value": [{"Ref_Key": "aaa"}]})
    page = await Catalog(infobase, "Goods").query()
    assert page.value[0]["Ref_Key"] == "aaa"
    assert "$format=json" in fake_odata.last["query"]
    assert fake_odata.last["accept"] == "application/json"


async def test_json_create_still_posts_json(fake_odata, infobase):
    fake_odata.respond(201, {"Ref_Key": "new"})
    created = await Catalog(infobase, "Goods").create({"Description": "X"})
    assert created["Ref_Key"] == "new"
    assert b'"Description"' in fake_odata.last["body"]
    assert "application/json" in fake_odata.last["content_type"]


async def test_atom_url_uses_format_atom(atom_infobase):
    url = atom_infobase.url("Catalog_Goods", top=1)
    assert "$format=atom" in url
    assert "$format=json" not in url


async def test_atom_register_virtual_table_uses_format_atom(fake_odata, atom_infobase):
    fake_odata.respond(200, ATOM_FEED, content_type="application/atom+xml")
    payload = await InformationRegister(atom_infobase, "Prices").slice_last()
    assert payload["value"][0]["Ref_Key"] == _GUID
    assert "$format=atom" in fake_odata.last["query"]
