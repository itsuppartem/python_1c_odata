# python-1c-odata

[![PyPI](https://img.shields.io/pypi/v/python-1c-odata.svg)](https://pypi.org/project/python-1c-odata/)
[![Python versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://github.com/itsuppartem/python_1c_odata)
[![CI](https://github.com/itsuppartem/python_1c_odata/actions/workflows/test.yml/badge.svg)](https://github.com/itsuppartem/python_1c_odata/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Async Python client for the **1C:Enterprise** standard OData 3.0 API (`/odata/standard.odata`). Catalogs, documents (post/unpost), registers, journals, charts of accounts, constants, exchange plans. Generic OData v4 clients usually break on 1C literals (`guid'...'`, `datetime'...'`) and virtual register tables.

Async-клиент стандартного OData-интерфейса **1С:Предприятие** (`/odata/standard.odata`).

Платформа говорит на **OData 3.0**: ключи `guid'...'`, даты `datetime'...'`, виртуальные таблицы регистров. Универсальные OData v4-библиотеки здесь обычно ломаются.

Homepage / repo: https://github.com/itsuppartem/python_1c_odata

## Install / Установка

```bash
pip install python-1c-odata
```

Python 3.10+ and aiohttp. For a clone: `pip install -e ".[dev]"`.

Нужен Python 3.10+ и aiohttp.

## Quick start / Быстрый старт

```python
import asyncio
from python_1c_odata import (
    AccumulationRegister,
    Catalog,
    Document,
    F,
    Infobase,
    InformationRegister,
    PostingMode,
    startswith,
)

async def main() -> None:
    async with Infobase("http://1c.example", "ut", "user", "password") as ib:
        goods = Catalog(ib, "Товары")
        page = await goods.query(
            top=10,
            select="Ref_Key,Description",
            odata_filter=(F("DeletionMark") == False) & (F("Цена") > 1000),
            inlinecount=True,
        )
        print(page.count, page.value)
        item = await goods.get("41aa6331-954f-11e3-814b-005056c00008")
        await goods.edit(
            item["Ref_Key"],
            {"Description": "Новое имя"},
            if_match=item.get("DataVersion"),
        )

        async for row in goods.iterate(
            page_size=100,
            odata_filter=startswith(F("Description"), "Сап"),
        ):
            print(row["Description"])

        orders = Document(ib, "ЗаказКлиента")
        created = await orders.create(
            {"Date": "2024-03-20T00:00:00"},
            posting_mode=PostingMode.POST,
        )
        await orders.unpost(created["Ref_Key"])

        rates = await InformationRegister(ib, "КурсыВалют").slice_last(
            period="2024-03-20T00:00:00",
            condition=F("Валюта_Key") == "guid'41aa6331-954f-11e3-814b-005056c00008'",
        )
        stock = await AccumulationRegister(ib, "ТоварыНаСкладах").balance(
            period="2024-03-20T00:00:00",
        )

asyncio.run(main())
```

You can skip `async with`: the session starts on the first request. Close it with `await ib.aclose()`.

Сессию можно не открывать через `async with`: тогда она создастся на первом запросе. Закройте её `await ib.aclose()`.

## Filter DSL / Фильтры

`query(odata_filter="DeletionMark eq false")` still works. The DSL is additive and emits OData 3.0 text (`eq` / `and` / `substringof`, plus `guid'...'` / `datetime'...'`).

`query(odata_filter="...")` как и раньше принимает строку. DSL — рядом, не вместо.

Parenthesize comparisons before `&` / `|` — Python bitwise operators bind tighter than `>` / `==`.

Сравнения в скобках: у `&` / `|` приоритет выше, чем у `>` / `==`.

```python
from datetime import datetime
from python_1c_odata import F, contains, endswith, guid, startswith, substringof

F("Цена") > 1000
(F("Цена") > 1000) & (F("DeletionMark") == False)
~F("DeletionMark")
F("Ref_Key") == guid("41aa6331-954f-11e3-814b-005056c00008")
F("Date") >= datetime(2024, 3, 20)
startswith(F("Description"), "Сап")
endswith(F("Description"), "ги")
substringof("Сапоги", F("Description"))
contains(F("Description"), "Сапоги")  # same as substringof (OData 3.0)

await goods.where(F("Цена") > 1000).top(10).select("Ref_Key").execute()
await goods.count(odata_filter=F("DeletionMark") == False)
```

## Debug

```python
ib = Infobase("http://1c.example", "ut", "user", "password", debug=True)
# or debug=print / any callable(str)
await Catalog(ib, "Товары").query(top=1)
print(ib.last_url, ib.last_status)
```

Logs **method**, URL with Cyrillic decoded, **status**, and duration in ms. The `Authorization` header is never written.

В лог: метод, URL (кириллица читаемая), статус, миллисекунды. Заголовок `Authorization` не пишется.

## What it does / Что умеет

| Object / Объект | Methods / Методы |
| --- | --- |
| Catalog | `query`, `iterate`, `count`, `get`, `create`, `edit` (PATCH), `replace` (PUT), `delete` |
| Document | same + `post` / `unpost`. Do not send `Posted` / `Проведен` — posting is a separate POST |
| Information register | `query` + `slice_last` / `slice_first` (`Period`, `Condition`) |
| Accumulation register | `query` + `balance` / `turnovers` / `balance_and_turnovers` |
| Accounting register | same virtual tables as accumulation (`AccountingRegister_*`) |
| Chart of accounts | same CRUD as a catalog (`ChartOfAccounts_*`) |
| Document journal | `query` / `get` / `iterate` / `count` only |
| Constant | `Constant_*` |
| Exchange plan | `ExchangePlan_*` |

Shared query options: `top`, `skip`, `select`, `odata_filter` (str or `F`), `expand`, `orderby`, `allowed_only` (1C RLS: `allowedOnly=true`), `inlinecount`.

`edit` / `replace` / `delete` accept `if_match=` and send `If-Match` (optimistic concurrency / `DataVersion`).

HTTP 4xx/5xx raise `ODataError`. 404 → `EntityNotFound`, 403 → `AccessDenied`, 412 → `ConcurrencyError`.

`$metadata` (XML): `await ib.metadata()`.
GUID in a filter: `guid("41aa-...")` → `guid'41aa-...'`.
Documents accept both `Date`/`Posted` and `Дата`/`Проведен`.

## What is still missing / Чего нет (пока)

| Missing | Notes |
| --- | --- |
| `$metadata` codegen | typed entity classes from EDM |
| BusinessProcess / Task / CalculationRegister | not wrapped this release |
| Sync client | this package is asyncio + aiohttp only |

## Development / Разработка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check src tests
mypy src
```
