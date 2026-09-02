"""URL prefixes for journals, accounting, constants, charts, exchange plans."""

import pytest

from python_1c_odata import (
    AccountingRegister,
    ChartOfAccounts,
    Constant,
    DocumentJournal,
    ExchangePlan,
)


async def test_chart_of_accounts_prefix(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await ChartOfAccounts(infobase, "Хозрасчетный").query(top=1)
    assert fake_odata.last["path"].endswith("ChartOfAccounts_Хозрасчетный")


async def test_document_journal_is_read_only_query(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    journal = DocumentJournal(infobase, "Продажи")
    await journal.query(top=5)
    assert fake_odata.last["path"].endswith("DocumentJournal_Продажи")
    with pytest.raises(TypeError, match="read-only"):
        await journal.create({"Date": "2024-01-01T00:00:00"})
    with pytest.raises(TypeError, match="read-only"):
        await journal.edit("41aa6331-954f-11e3-814b-005056c00008", {"Number": "1"})
    assert len(fake_odata.requests) == 1


async def test_constant_prefix(fake_odata, infobase):
    fake_odata.respond(200, {"value": [{"Value": True}]})
    await Constant(infobase, "ИспользоватьХарактеристики").query()
    assert fake_odata.last["path"].endswith("Constant_ИспользоватьХарактеристики")


async def test_exchange_plan_key_url(fake_odata, infobase):
    fake_odata.respond(200, {"Description": "Узел"})
    await ExchangePlan(infobase, "ОбменССайтом").get("41aa6331-954f-11e3-814b-005056c00008")
    assert fake_odata.last["path"].endswith(
        "ExchangePlan_ОбменССайтом(guid'41aa6331-954f-11e3-814b-005056c00008')"
    )


async def test_accounting_balance(fake_odata, infobase):
    fake_odata.respond(200, {"value": [{"СуммаBalance": 10}]})
    payload = await AccountingRegister(infobase, "Хозрасчетный").balance(
        period="2024-03-20T00:00:00",
        condition="Счет eq '41'",
    )
    assert payload["value"][0]["СуммаBalance"] == 10
    assert fake_odata.last["path"].endswith(
        "AccountingRegister_Хозрасчетный/Balance("
        "Period=datetime'2024-03-20T00:00:00',Condition='Счет eq '41'')"
    )


async def test_accounting_turnovers_and_balance_and_turnovers(fake_odata, infobase):
    fake_odata.respond(200, {"value": []})
    await AccountingRegister(infobase, "Хозрасчетный").turnovers(
        start_period="2024-01-01T00:00:00",
        end_period="2024-02-01T00:00:00",
    )
    assert fake_odata.last["path"].endswith(
        "AccountingRegister_Хозрасчетный/Turnovers("
        "StartPeriod=datetime'2024-01-01T00:00:00',EndPeriod=datetime'2024-02-01T00:00:00')"
    )
    await AccountingRegister(infobase, "Хозрасчетный").balance_and_turnovers(
        start_period="2024-01-01T00:00:00",
        end_period="2024-02-01T00:00:00",
        condition="Счет eq '41'",
    )
    assert fake_odata.last["path"].endswith(
        "AccountingRegister_Хозрасчетный/BalanceAndTurnovers("
        "StartPeriod=datetime'2024-01-01T00:00:00',"
        "EndPeriod=datetime'2024-02-01T00:00:00',"
        "Condition='Счет eq '41'')"
    )


async def test_accounting_has_no_slice_last():
    assert not hasattr(AccountingRegister, "slice_last")
