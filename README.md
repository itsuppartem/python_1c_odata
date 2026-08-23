# python-1c-odata

Async-клиент стандартного OData-интерфейса **1С:Предприятие** (`/odata/standard.odata`).

Платформа говорит на **OData 3.0**: ключи `guid'...'`, даты `datetime'...'`, виртуальные таблицы регистров. Универсальные OData v4-библиотеки здесь обычно ломаются.

## Установка

```bash
pip install -e .
```

Нужен Python 3.10+ и aiohttp.

## Быстрый старт

```python
import asyncio
from python_1c_odata import (
    AccumulationRegister,
    Catalog,
    Document,
    Infobase,
    InformationRegister,
    PostingMode,
)

async def main() -> None:
    async with Infobase("http://1c.example", "ut", "user", "password") as ib:
        goods = Catalog(ib, "Товары")
        page = await goods.query(
            top=10,
            select="Ref_Key,Description",
            odata_filter="DeletionMark eq false",
        )
        item = await goods.get("41aa6331-954f-11e3-814b-005056c00008")
        await goods.edit(item["Ref_Key"], {"Description": "Новое имя"})

        orders = Document(ib, "ЗаказКлиента")
        created = await orders.create(
            {"Date": "2024-03-20T00:00:00"},
            posting_mode=PostingMode.POST,
        )
        await orders.unpost(created["Ref_Key"])

        rates = await InformationRegister(ib, "КурсыВалют").slice_last(
            period="2024-03-20T00:00:00",
            condition="Валюта_Key eq guid'41aa6331-954f-11e3-814b-005056c00008'",
        )
        stock = await AccumulationRegister(ib, "ТоварыНаСкладах").balance(
            period="2024-03-20T00:00:00",
        )

asyncio.run(main())
```

Сессию можно не открывать через `async with`: тогда она создастся на первом запросе. Закройте её `await ib.aclose()`.

## Что умеет

| Объект | Методы |
| --- | --- |
| Справочник `Catalog` | `query`, `get`, `create`, `edit` (PATCH), `replace` (PUT), `delete` |
| Документ `Document` | то же + `post` / `unpost`. Поле `Posted` в теле писать нельзя — проведение отдельным POST |
| Регистр сведений | `query` + `slice_last` / `slice_first` (`Period`, `Condition`) |
| Регистр накопления | `query` + `balance` / `turnovers` / `balance_and_turnovers` |

Общие параметры выборки: `top`, `skip`, `select`, `odata_filter`, `expand`, `orderby`.

Ошибки HTTP 4xx/5xx — `ODataError` со статусом и текстом 1С, не «голый» `Exception`.

## Чего нет (пока)

- DSL для `$filter` (строка фильтра — ваша)
- генерация типов из `$metadata`
- журналы, бухгалтерия, расчёт, бизнес-процессы
- синхронный клиент

## Разработка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```
