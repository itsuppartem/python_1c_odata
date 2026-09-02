"""@odata.bind and ValueStorage _Base64Data field names."""

from python_1c_odata import base64_data, bind_field, odata_bind

_REF = "41aa6331-954f-11e3-814b-005056c00008"


def test_odata_bind_wraps_guid():
    assert odata_bind("Catalog_Организации", _REF) == f"Catalog_Организации(guid'{_REF}')"


def test_odata_bind_composite_key():
    assert odata_bind(
        "InformationRegister_Цены_RecordType",
        {"Товар_Key": _REF, "ТипЦены": "Розничная"},
    ) == (
        "InformationRegister_Цены_RecordType("
        f"Товар_Key=guid'{_REF}',ТипЦены='Розничная')"
    )


def test_base64_data_suffix():
    assert base64_data("Файл") == "Файл_Base64Data"
    assert base64_data("Файл_Base64Data") == "Файл_Base64Data"


def test_bind_field_dict_fragment():
    assert bind_field("Организация", "Catalog_Организации", _REF) == {
        "Организация@odata.bind": f"Catalog_Организации(guid'{_REF}')",
    }
