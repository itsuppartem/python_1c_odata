"""URL assembly for 1C OData 3.0. Breaks if slashes, keys, or $params are glued wrong."""

import pytest

from python_1c_odata.url import (
    accumulation_virtual_path,
    calculation_virtual_path,
    entity_key,
    entity_path,
    infobase_root,
    key_path,
    query_string,
    slice_path,
)


def test_root_joins_server_and_infobase_without_double_slashes():
    assert infobase_root("http://host/", "/ut/") == "http://host/ut/odata/standard.odata"


def test_root_keeps_https_and_port():
    assert infobase_root("https://1c.example:443", "erp") == (
        "https://1c.example:443/erp/odata/standard.odata"
    )


def test_entity_path_uses_1c_prefix():
    assert entity_path("http://h/ib/odata/standard.odata", "Catalog_Товары") == (
        "http://h/ib/odata/standard.odata/Catalog_Товары"
    )


def test_key_path_uses_odata_v3_guid_literal():
    url = key_path(
        "http://h/ib/odata/standard.odata",
        "Document_Заказ",
        "41aa6331-954f-11e3-814b-005056c00008",
    )
    assert url.endswith("Document_Заказ(guid'41aa6331-954f-11e3-814b-005056c00008')")


def test_composite_key_path_joins_named_parts():
    url = key_path(
        "http://h/ib/odata/standard.odata",
        "InformationRegister_Цены_RecordType",
        {"Товар_Key": "guid'aaa'", "ТипЦены": "'Розничная'"},
    )
    assert url.endswith(
        "InformationRegister_Цены_RecordType(Товар_Key=guid'aaa',ТипЦены='Розничная')"
    )


def test_query_string_starts_with_format_json_and_appends_odata_options():
    qs = query_string(
        top=10,
        skip=5,
        select="Ref_Key,Description",
        odata_filter="DeletionMark eq false",
        expand="Владелец",
        orderby="Description",
    )
    assert qs.startswith("?$format=json")
    assert "$top=10" in qs
    assert "$skip=5" in qs
    assert "$select=Ref_Key,Description" in qs
    assert "$filter=DeletionMark%20eq%20false" in qs
    assert "$expand=" in qs
    assert "$orderby=Description" in qs


def test_query_string_omits_none_options():
    qs = query_string(top=1)
    assert "$skip" not in qs
    assert "$filter" not in qs
    assert qs == "?$format=json&$top=1"


def test_query_string_atom_format():
    qs = query_string(odata_format="atom", top=1)
    assert qs == "?$format=atom&$top=1"


def test_query_string_rejects_unknown_format():
    with pytest.raises(ValueError):
        query_string(odata_format="auto")


def test_query_string_keeps_guid_and_datetime_quotes_in_filter():
    qs = query_string(
        odata_filter="Ref_Key eq guid'41aa6331-954f-11e3-814b-005056c00008'"
        " and Date ge datetime'2024-01-01T00:00:00'"
    )
    assert "guid'41aa6331-954f-11e3-814b-005056c00008'" in qs
    assert "datetime'2024-01-01T00:00:00'" in qs


def test_slice_path_empty_args_are_empty_parens():
    url = slice_path("http://h/ib/odata/standard.odata", "InformationRegister_Курсы", "SliceLast")
    assert url.endswith("InformationRegister_Курсы/SliceLast()")


def test_slice_path_named_period_and_condition():
    url = slice_path(
        "http://h/ib/odata/standard.odata",
        "InformationRegister_Курсы",
        "SliceLast",
        period="datetime'2024-03-20T00:00:00'",
        condition="Валюта_Key eq guid'aaa'",
    )
    assert "SliceLast(Period=datetime'2024-03-20T00:00:00',Condition='Валюта_Key eq guid'aaa'')" in url


def test_accumulation_balance_and_turnovers_use_named_period_params():
    url = accumulation_virtual_path(
        "http://h/ib/odata/standard.odata",
        "AccumulationRegister_ТоварыНаСкладах",
        "BalanceAndTurnovers",
        start_period="datetime'2024-01-01T00:00:00'",
        end_period="datetime'2024-02-01T00:00:00'",
        condition="Склад_Key eq guid'aaa'",
    )
    assert url.endswith(
        "AccumulationRegister_ТоварыНаСкладах/BalanceAndTurnovers("
        "StartPeriod=datetime'2024-01-01T00:00:00',"
        "EndPeriod=datetime'2024-02-01T00:00:00',"
        "Condition='Склад_Key eq guid'aaa'')"
    )


def test_entity_key_matches_bind_form():
    assert entity_key("Catalog_Организации", "41aa6331-954f-11e3-814b-005056c00008") == (
        "Catalog_Организации(guid'41aa6331-954f-11e3-814b-005056c00008')"
    )


def test_calculation_virtual_path_recalculation_and_base():
    root = "http://h/ib/odata/standard.odata"
    recalc = calculation_virtual_path(
        root,
        "CalculationRegister_Начисления",
        "Recalculation",
        condition="Recorder_Key eq guid'aaa'",
    )
    assert recalc.endswith(
        "CalculationRegister_Начисления/Recalculation(Condition='Recorder_Key eq guid'aaa'')"
    )
    base = calculation_virtual_path(
        root,
        "CalculationRegister_Начисления",
        "Base",
        condition="ФизЛицо_Key eq guid'aaa'",
        main_register_dimensions="ФизЛицо",
        base_register_dimensions="Сотрудник",
        view_points="Результат",
    )
    assert base.endswith(
        "CalculationRegister_Начисления/Base("
        "Condition='ФизЛицо_Key eq guid'aaa'',"
        "MainRegisterDimensions='ФизЛицо',"
        "BaseRegisterDimensions='Сотрудник',"
        "ViewPoints='Результат')"
    )


def test_calculation_virtual_path_condition_only():
    url = calculation_virtual_path(
        "http://h/ib/odata/standard.odata",
        "CalculationRegister_Начисления",
        "ScheduledData",
        condition="Recorder_Key eq guid'aaa'",
    )
    assert url.endswith(
        "CalculationRegister_Начисления/ScheduledData(Condition='Recorder_Key eq guid'aaa'')"
    )
    empty = calculation_virtual_path(
        "http://h/ib/odata/standard.odata",
        "CalculationRegister_Начисления",
        "ActualActionPeriod",
    )
    assert empty.endswith("CalculationRegister_Начисления/ActualActionPeriod()")


def test_query_string_rejects_non_int_top():
    with pytest.raises(TypeError):
        query_string(top="10")


def test_query_string_adds_1c_allowed_only_and_inlinecount():
    qs = query_string(allowed_only=True, inlinecount=True)
    assert "allowedOnly=true" in qs
    assert "$inlinecount=allpages" in qs


def test_composite_key_wraps_bare_uuid_and_quotes_plain_string():
    url = key_path(
        "http://h/ib/odata/standard.odata",
        "InformationRegister_Цены_RecordType",
        {
            "Товар_Key": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "ТипЦены": "Розничная",
        },
    )
    assert url.endswith(
        "InformationRegister_Цены_RecordType("
        "Товар_Key=guid'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',ТипЦены='Розничная')"
    )
