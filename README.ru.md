# python-1c-odata

[English](README.md) | Русский

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

## JSON и Atom

По умолчанию JSON (`$format=json`). Так отвечает 1С:Предприятие 8.3.6 и новее.

Публикации 8.3.5 говорят только Atom/XML. Передайте `format="atom"`: клиент шлёт `$format=atom`, `Accept: application/atom+xml` и тела `<entry>` (`DataServiceVersion: 3.0`).

`format="auto"` по-прежнему *просит* JSON. Если сервер отвечает Atom (Content-Type или тело `<feed>` / `<entry>` / `<m:error>`), клиент это разбирает. Так можно зайти, когда неизвестно, 8.3.5 это или нет.

```python
async with Infobase("http://1c.example", "ut", "user", "password", format="atom") as ib:
    page = await Catalog(ib, "Товары").query(top=10)

async with Infobase("http://1c.example", "ut", "user", "password", format="auto") as ib:
    page = await Catalog(ib, "Товары").query(top=10)
```

`@odata.bind` на записи — только JSON. В Atom такие ключи пропускаются.

Кодек Atom **не** добавляет `$skip` и `$inlinecount` в 8.3.5. Если вы их всё же укажете, они уйдут в URL, и платформа ответит ошибкой.

| 1С:Предприятие | Формат | Что умеет этот клиент |
| --- | --- | --- |
| 8.3.5 | только Atom | `format="atom"` или `format="auto"`. Базовые `query` / `get` / `create` / `edit`. Нет `iterate` / `count` / `any` / `all` / представлений / `$expand` |
| 8.3.6+ | есть JSON | `format="json"` по умолчанию |
| 8.3.8+ | `$skip`, `$inlinecount`, `any` / `all` | `iterate`, `count`, фильтры табличных частей |
| 8.3.9+ | `$expand`, `____Presentation` | `expand=`, `presentations=True` |

Не поддерживаются: 8.2, 7.7, SOAP, COM, произвольные HTTP-сервисы (`/hs/`), OData 4.

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

HTTP 4xx/5xx поднимают `ODataError`. 404 → `EntityNotFound`, 403 → `AccessDenied`, 412 → `ConcurrencyError`. `ODataError.internal_code` заполняется из `odata.error.code` / `error.code` / Atom `<m:code>`, если 1С его присылает.

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
| 8.2 / SOAP / COM / `/hs/` / OData 4 | вне задачи. Самая старая публикация — Atom 8.3.5 |

## Разработка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check src tests
mypy src
```
