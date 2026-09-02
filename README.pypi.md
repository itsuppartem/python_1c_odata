English | [Русский](#russkiy)

# python-1c-odata

[![PyPI](https://img.shields.io/pypi/v/python-1c-odata.svg)](https://pypi.org/project/python-1c-odata/)
[![Python versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://github.com/itsuppartem/python_1c_odata)
[![CI](https://github.com/itsuppartem/python_1c_odata/actions/workflows/test.yml/badge.svg)](https://github.com/itsuppartem/python_1c_odata/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Async Python client for the **1C:Enterprise** standard OData 3.0 API (`/odata/standard.odata`). Catalogs, documents (post/unpost), registers, journals, charts, constants, exchange plans, business processes, tasks. Generic OData v4 clients usually break on 1C literals (`guid'...'`, `datetime'...'`) and virtual register tables.

Homepage / repo: https://github.com/itsuppartem/python_1c_odata

## Install

```bash
pip install python-1c-odata
```

Python 3.10+ and aiohttp. For a clone: `pip install -e ".[dev]"`.

## Quick start

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
            select=["Ref_Key", "Description"],
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

## Filter DSL

`query(odata_filter="DeletionMark eq false")` still works. The DSL is additive and emits OData 3.0 text (`eq` / `and` / `substringof`, plus `guid'...'` / `datetime'...'`).

Parenthesize comparisons before `&` / `|` — Python bitwise operators bind tighter than `>` / `==`.

```python
from datetime import datetime
from python_1c_odata import F, cast, contains, endswith, guid, isof, startswith, substringof

F("Цена") > 1000
(F("Цена") > 1000) & (F("DeletionMark") == False)
~F("DeletionMark")
F("Ref_Key") == guid("41aa6331-954f-11e3-814b-005056c00008")
F("Date") >= datetime(2024, 3, 20)
startswith(F("Description"), "Сап")
endswith(F("Description"), "ги")
substringof("Сапоги", F("Description"))
contains(F("Description"), "Сапоги")  # same as substringof (OData 3.0)
isof(F("Поле"), "Edm.String")
cast(F("Сумма"), "Edm.Decimal") > 0

await goods.where(F("Цена") > 1000).top(10).select("Ref_Key").execute()
await goods.count(odata_filter=F("DeletionMark") == False)

# tabular sections
F("Товары").any(F("Цена") > 10000)   # Товары/any(d: d/Цена gt 10000)
F("Товары").all(F("Количество") > 0)
```

## Presentations

1C exposes `Name____Presentation` (four underscores). `$select=*, *____Presentation` returns values and presentations.

```python
from python_1c_odata import ALL_PRESENTATIONS, presentation

presentation("Контрагент")  # Контрагент____Presentation
ALL_PRESENTATIONS           # *____Presentation

await goods.query(select="*", presentations=True)
# $select=*,*____Presentation
await goods.query(select=["Ref_Key", presentation("Контрагент")])
print(goods.url(select="*", presentations=True))  # no HTTP request
```

## @odata.bind and ValueStorage

Use on PUT/replace (and other writes) to point at an existing entity, or to fill a ValueStorage field.

```python
from python_1c_odata import base64_data, bind_field, odata_bind

odata_bind("Catalog_Организации", "41aa6331-954f-11e3-814b-005056c00008")
# Catalog_Организации(guid'41aa6331-...')

await goods.replace(
    ref,
    {
        **bind_field("Организация", "Catalog_Организации", org_key),
        base64_data("Файл"): file_b64,
    },
)
```

## Data load mode

Header `1C_OData-DataLoadMode: true` emulates `ОбменДанными.Загрузка`. Sent only on POST/PATCH/PUT/DELETE.

```python
ib = Infobase("http://1c.example", "ut", "user", "password", data_load_mode=True)
await Catalog(ib, "Товары").create({"Description": "X"}, data_load_mode=True)  # this request only
```

## Metadata (no codegen)

```python
names = await ib.entity_sets()
info = await ib.entity_type_for_set("Catalog_Товары")
info.keys          # ("Ref_Key",)
info.properties    # name / type / nullable
```

HTTP 4xx/5xx raise `ODataError`. 404 → `EntityNotFound`, 403 → `AccessDenied`, 412 → `ConcurrencyError`. `ODataError.internal_code` is filled from `odata.error.code` / `error.code` when 1C sends it.

## Debug

```python
ib = Infobase("http://1c.example", "ut", "user", "password", debug=True)
# or debug=print / any callable(str)
await Catalog(ib, "Товары").query(top=1)
print(ib.last_url, ib.last_status)
```

Logs **method**, URL with Cyrillic decoded, **status**, and duration in ms. The `Authorization` header is never written.

## What it does

| Object | Methods |
| --- | --- |
| Catalog | `query`, `iterate`, `count`, `get`, `create`, `edit` (PATCH), `replace` (PUT), `delete` |
| Document | same + `post` / `unpost`. Do not send `Posted` / `Проведен` — posting is a separate POST |
| Information register | `query` + `slice_last` / `slice_first` (`Period`, `Condition`) |
| Accumulation register | `query` + `balance` / `turnovers` / `balance_and_turnovers` |
| Accounting register | same virtual tables as accumulation (`AccountingRegister_*`) |
| Chart of accounts | same CRUD as a catalog (`ChartOfAccounts_*`) |
| Chart of characteristic types | same CRUD (`ChartOfCharacteristicTypes_*`) |
| Chart of calculation types | same CRUD (`ChartOfCalculationTypes_*`) |
| Business process | same CRUD + `start` (POST `Start`, optional `RoutePoint`) |
| Task | same CRUD + `execute` (POST `ExecuteTask`) |
| Calculation register | `query` + `schedule_data` / `actual_action_period` / `recalculation` / `base` (`ScheduledData`, `ActualActionPeriod`, `Recalculation`, `Base`) |
| Document journal | `query` / `get` / `iterate` / `count` only |
| Enumeration | `query` / `get` / `iterate` / `count` only (`Enumeration_*`) |
| Constant | `Constant_*` |
| Exchange plan | `ExchangePlan_*` |

Shared query options: `top`, `skip`, `select`, `odata_filter` (str or `F`), `expand`, `orderby`, `allowed_only` (1C RLS: `allowedOnly=true`), `inlinecount`.

`edit` / `replace` / `delete` accept `if_match=` and send `If-Match` (optimistic concurrency / `DataVersion`).

`$metadata` (XML): `await ib.metadata()`. Entity set names and types (cached after the first fetch):

```python
from python_1c_odata import BusinessProcess, CalculationRegister, Catalog, Enumeration, Task

names = await ib.entity_sets()
if await ib.has_entity_set("Catalog_Товары"):
    goods = Catalog(ib, "Товары")
    info = await ib.entity_type_for_set("Catalog_Товары")

await Enumeration(ib, "СтавкиНДС").query(top=20)
await BusinessProcess(ib, "СогласованиеЗаказа").start(ref)
await Task(ib, "ЗадачаИсполнителя").execute(ref)
await CalculationRegister(ib, "Начисления").schedule_data(
    condition="Recorder_Key eq guid'41aa6331-954f-11e3-814b-005056c00008'",
)
await CalculationRegister(ib, "Начисления").recalculation(condition="...")
await CalculationRegister(ib, "Начисления").base(
    condition="...",
    main_register_dimensions="ФизЛицо,Организация",
    base_register_dimensions="Сотрудник,Организация",
    view_points="Результат",
)
```

GUID in a filter: `guid("41aa-...")` → `guid'41aa-...'`.
Documents accept both `Date`/`Posted` and `Дата`/`Проведен`.

## What is still missing

| Missing | Notes |
| --- | --- |
| Full `$metadata` codegen | typed Python classes from EDM (parse + `entity_type_for_set` only) |
| Sync client | this package is asyncio + aiohttp only |

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check src tests
mypy src
```

---

<h2 id="russkiy">Русский</h2>

# python-1c-odata

[English](#python-1c-odata) | Русский

[![PyPI](https://img.shields.io/pypi/v/python-1c-odata.svg)](https://pypi.org/project/python-1c-odata/)
[![Python versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://github.com/itsuppartem/python_1c_odata)
[![CI](https://github.com/itsuppartem/python_1c_odata/actions/workflows/test.yml/badge.svg)](https://github.com/itsuppartem/python_1c_odata/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Асинхронный Python-клиент стандартного OData-интерфейса **1С:Предприятие** (`/odata/standard.odata`). Справочники, документы (проведение и отмена проведения), регистры, журналы, планы счетов и видов, константы, планы обмена, бизнес-процессы, задачи.

Платформа говорит на **OData 3.0**: ключи `guid'...'`, даты `datetime'...'`, виртуальные таблицы регистров. Универсальные OData v4-библиотеки здесь обычно ломаются.

Репозиторий: https://github.com/itsuppartem/python_1c_odata

## Установка

```bash
pip install python-1c-odata
```

Нужен Python 3.10+ и aiohttp. Для клона: `pip install -e ".[dev]"`.

## Быстрый старт

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
            select=["Ref_Key", "Description"],
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

Сессию можно не открывать через `async with`: тогда она создастся на первом запросе. Закройте её `await ib.aclose()`.

## Фильтры

`query(odata_filter="DeletionMark eq false")` по-прежнему принимает строку. DSL — рядом, не вместо: он добавляет OData 3.0-текст (`eq` / `and` / `substringof`, плюс `guid'...'` / `datetime'...'`).

Сравнения берите в скобки перед `&` / `|`: у побитовых операторов Python приоритет выше, чем у `>` / `==`.

```python
from datetime import datetime
from python_1c_odata import F, cast, contains, endswith, guid, isof, startswith, substringof

F("Цена") > 1000
(F("Цена") > 1000) & (F("DeletionMark") == False)
~F("DeletionMark")
F("Ref_Key") == guid("41aa6331-954f-11e3-814b-005056c00008")
F("Date") >= datetime(2024, 3, 20)
startswith(F("Description"), "Сап")
endswith(F("Description"), "ги")
substringof("Сапоги", F("Description"))
contains(F("Description"), "Сапоги")  # то же, что substringof (OData 3.0)
isof(F("Поле"), "Edm.String")
cast(F("Сумма"), "Edm.Decimal") > 0

await goods.where(F("Цена") > 1000).top(10).select("Ref_Key").execute()
await goods.count(odata_filter=F("DeletionMark") == False)

# табличные части
F("Товары").any(F("Цена") > 10000)   # Товары/any(d: d/Цена gt 10000)
F("Товары").all(F("Количество") > 0)
```

## Представления

У 1С поле представления — `Имя____Presentation` (четыре подчёркивания). `$select=*, *____Presentation` возвращает значения и представления.

```python
from python_1c_odata import ALL_PRESENTATIONS, presentation

presentation("Контрагент")  # Контрагент____Presentation
ALL_PRESENTATIONS           # *____Presentation

await goods.query(select="*", presentations=True)
# $select=*,*____Presentation
await goods.query(select=["Ref_Key", presentation("Контрагент")])
print(goods.url(select="*", presentations=True))  # без HTTP-запроса
```

## @odata.bind и ValueStorage

На PUT/replace (и других записях) можно указать ссылку на существующий объект или заполнить поле хранилища значений.

```python
from python_1c_odata import base64_data, bind_field, odata_bind

odata_bind("Catalog_Организации", "41aa6331-954f-11e3-814b-005056c00008")
# Catalog_Организации(guid'41aa6331-...')

await goods.replace(
    ref,
    {
        **bind_field("Организация", "Catalog_Организации", org_key),
        base64_data("Файл"): file_b64,
    },
)
```

## Режим загрузки

Заголовок `1C_OData-DataLoadMode: true` имитирует `ОбменДанными.Загрузка`. Уходит только на POST/PATCH/PUT/DELETE. По умолчанию выключен.

```python
ib = Infobase("http://1c.example", "ut", "user", "password", data_load_mode=True)
await Catalog(ib, "Товары").create({"Description": "X"}, data_load_mode=True)  # только этот запрос
```

## Метаданные (без кодогенерации)

```python
names = await ib.entity_sets()
info = await ib.entity_type_for_set("Catalog_Товары")
info.keys          # ("Ref_Key",)
info.properties    # name / type / nullable
```

HTTP 4xx/5xx поднимают `ODataError`. 404 → `EntityNotFound`, 403 → `AccessDenied`, 412 → `ConcurrencyError`. `ODataError.internal_code` заполняется из `odata.error.code` / `error.code`, если 1С его присылает.

## Отладка

```python
ib = Infobase("http://1c.example", "ut", "user", "password", debug=True)
# или debug=print / любой callable(str)
await Catalog(ib, "Товары").query(top=1)
print(ib.last_url, ib.last_status)
```

В лог: **метод**, URL (кириллица читаемая), **статус**, длительность в миллисекундах. Заголовок `Authorization` не пишется.

## Что умеет

| Объект | Методы |
| --- | --- |
| Catalog | `query`, `iterate`, `count`, `get`, `create`, `edit` (PATCH), `replace` (PUT), `delete` |
| Document | то же + `post` / `unpost`. Не передавайте `Posted` / `Проведен` — проведение это отдельный POST |
| Регистр сведений | `query` + `slice_last` / `slice_first` (`Period`, `Condition`) |
| Регистр накопления | `query` + `balance` / `turnovers` / `balance_and_turnovers` |
| Регистр бухгалтерии | те же виртуальные таблицы, что у накопления (`AccountingRegister_*`) |
| План счетов | тот же CRUD, что у справочника (`ChartOfAccounts_*`) |
| План видов характеристик | тот же CRUD (`ChartOfCharacteristicTypes_*`) |
| План видов расчёта | тот же CRUD (`ChartOfCalculationTypes_*`) |
| Бизнес-процесс | тот же CRUD + `start` (POST `Start`, необязательный `RoutePoint`) |
| Задача | тот же CRUD + `execute` (POST `ExecuteTask`) |
| Регистр расчёта | `query` + `schedule_data` / `actual_action_period` / `recalculation` / `base` (`ScheduledData`, `ActualActionPeriod`, `Recalculation`, `Base`) |
| Журнал документов | только `query` / `get` / `iterate` / `count` |
| Перечисление | только `query` / `get` / `iterate` / `count` (`Enumeration_*`) |
| Константа | `Constant_*` |
| План обмена | `ExchangePlan_*` |

Общие параметры запроса: `top`, `skip`, `select`, `odata_filter` (строка или `F`), `expand`, `orderby`, `allowed_only` (RLS 1С: `allowedOnly=true`), `inlinecount`.

`edit` / `replace` / `delete` принимают `if_match=` и отправляют `If-Match` (оптимистичная блокировка / `DataVersion`).

`$metadata` (XML): `await ib.metadata()`. Имена наборов и типы (кэш после первого запроса):

```python
from python_1c_odata import BusinessProcess, CalculationRegister, Catalog, Enumeration, Task

names = await ib.entity_sets()
if await ib.has_entity_set("Catalog_Товары"):
    goods = Catalog(ib, "Товары")
    info = await ib.entity_type_for_set("Catalog_Товары")

await Enumeration(ib, "СтавкиНДС").query(top=20)
await BusinessProcess(ib, "СогласованиеЗаказа").start(ref)
await Task(ib, "ЗадачаИсполнителя").execute(ref)
await CalculationRegister(ib, "Начисления").schedule_data(
    condition="Recorder_Key eq guid'41aa6331-954f-11e3-814b-005056c00008'",
)
await CalculationRegister(ib, "Начисления").recalculation(condition="...")
await CalculationRegister(ib, "Начисления").base(
    condition="...",
    main_register_dimensions="ФизЛицо,Организация",
    base_register_dimensions="Сотрудник,Организация",
    view_points="Результат",
)
```

GUID в фильтре: `guid("41aa-...")` → `guid'41aa-...'`.
Документы принимают и `Date`/`Posted`, и `Дата`/`Проведен`.

## Чего пока нет

| Нет | Комментарий |
| --- | --- |
| Полная кодогенерация из `$metadata` | типизированные классы Python из EDM (пока только разбор + `entity_type_for_set`) |
| Синхронный клиент | пакет только asyncio + aiohttp |

## Разработка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check src tests
mypy src
```
