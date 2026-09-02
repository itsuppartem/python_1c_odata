"""OData 3.0 filter DSL. Breaks if operators emit v4 or drop 1C literals."""

from datetime import datetime
from uuid import UUID

import pytest

from python_1c_odata import (
    F,
    all_,
    any_,
    cast,
    contains,
    endswith,
    guid,
    isof,
    startswith,
    substringof,
)
from python_1c_odata.filter import Filter


def test_comparison_and_bool_and_null():
    assert str(F("Цена") > 1000) == "Цена gt 1000"
    assert str(F("Цена") >= 10.5) == "Цена ge 10.5"
    assert str(F("DeletionMark").eq(False)) == "DeletionMark eq false"
    assert str(F("Owner_Key").eq(None)) == "Owner_Key eq null"


def test_guid_and_datetime_literals():
    ref = "41aa6331-954f-11e3-814b-005056c00008"
    assert str(F("Ref_Key") == guid(ref)) == f"Ref_Key eq guid'{ref}'"
    assert str(F("Ref_Key") == UUID(ref)) == f"Ref_Key eq guid'{ref}'"
    assert str(F("Date") >= datetime(2024, 3, 20, 0, 0, 0)) == (
        "Date ge datetime'2024-03-20T00:00:00'"
    )
    assert str(F("Ref_Key") == f"guid'{ref}'") == f"Ref_Key eq guid'{ref}'"


def test_string_quotes_are_odata_escaped():
    assert str(F("Description") == "O'Brien") == "Description eq 'O''Brien'"


def test_logical_ops_parenthesize():
    expr = (F("Цена") > 1000) & F("DeletionMark").eq(False)
    assert str(expr) == "(Цена gt 1000) and (DeletionMark eq false)"
    expr = (F("Цена") < 10) | (F("Цена") > 100)
    assert str(expr) == "(Цена lt 10) or (Цена gt 100)"
    assert str(~F("DeletionMark")) == "not (DeletionMark)"


def test_and_or_methods():
    expr = F("Цена").gt(1000).and_(F("Код").eq("A"))
    assert str(expr) == "(Цена gt 1000) and (Код eq 'A')"


def test_string_functions_are_odata3():
    assert str(startswith(F("Description"), "Сап")) == "startswith(Description, 'Сап')"
    assert str(endswith("Description", "ги")) == "endswith(Description, 'ги')"
    assert str(substringof("Сапоги", F("Description"))) == "substringof('Сапоги', Description)"
    assert str(contains(F("Description"), "Сапоги")) == "substringof('Сапоги', Description)"
    assert str(F("Description").startswith("Сап")) == "startswith(Description, 'Сап')"


def test_field_on_rhs_is_not_quoted():
    assert str(F("Цена") == F("ЦенаСтарая")) == "Цена eq ЦенаСтарая"


def test_unsupported_literal_raises():
    with pytest.raises(TypeError):
        str(F("X") == object())


def test_filter_repr_contains_text():
    assert "Цена gt 1" in repr(F("Цена") > 1)
    assert isinstance(F("Цена") > 1, Filter)


def test_isof_and_cast_are_odata3():
    assert str(isof(F("Поле"), "Edm.String")) == "isof(Поле, 'Edm.String')"
    assert str(cast("Сумма", "Edm.Decimal")) == "cast(Сумма, 'Edm.Decimal')"
    assert str(F("Поле").isof("Edm.String")) == "isof(Поле, 'Edm.String')"
    assert str(F("Сумма").cast("Edm.Int32") > 0) == "cast(Сумма, 'Edm.Int32') gt 0"
    assert str(isof(F("Поле"), "'Edm.String'")) == "isof(Поле, 'Edm.String')"


def test_any_all_tabular_section_uses_lambda_d():
    assert str(F("Товары").any(F("Цена") > 10000)) == "Товары/any(d: d/Цена gt 10000)"
    assert str(F("Товары").all(F("Цена") > 10000)) == "Товары/all(d: d/Цена gt 10000)"
    assert str(any_(F("Товары"), F("Цена") > 10000)) == "Товары/any(d: d/Цена gt 10000)"
    assert str(all_("Товары", F("Количество") > 0)) == "Товары/all(d: d/Количество gt 0)"


def test_any_prefixes_compound_and_guid_fields():
    ref = "41aa6331-954f-11e3-814b-005056c00008"
    expr = F("Товары").any((F("Цена") > 10000) & (F("Номенклатура_Key") == guid(ref)))
    assert str(expr) == (
        f"Товары/any(d: (d/Цена gt 10000) and (d/Номенклатура_Key eq guid'{ref}'))"
    )
    already = F("Товары").any("d/Цена gt 1")
    assert str(already) == "Товары/any(d: d/Цена gt 1)"
