"""1C OData v3 literals. Breaks if guid/datetime are emitted as OData v4."""

from datetime import datetime

import pytest

from python_1c_odata.literals import odata_datetime, parse_guid


def test_parse_guid_normalizes_uuid_text():
    assert parse_guid("41AA6331-954F-11E3-814B-005056C00008") == "41aa6331-954f-11e3-814b-005056c00008"


def test_parse_guid_rejects_garbage():
    with pytest.raises(ValueError):
        parse_guid("not-a-guid")


def test_odata_datetime_from_datetime_is_naive_iso_in_v3_quotes():
    assert odata_datetime(datetime(2024, 3, 20, 15, 30, 1)) == "datetime'2024-03-20T15:30:01'"


def test_odata_datetime_wraps_bare_iso_string():
    assert odata_datetime("2024-03-20T00:00:00") == "datetime'2024-03-20T00:00:00'"


def test_guid_literal_wraps_parsed_uuid():
    from python_1c_odata.literals import guid

    assert guid("41AA6331-954F-11E3-814B-005056C00008") == "guid'41aa6331-954f-11e3-814b-005056c00008'"
