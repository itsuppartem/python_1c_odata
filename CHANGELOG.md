# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-09-02

### Added

- Entity types: `BusinessProcess` (`start` → POST `Start`, optional `RoutePoint`), `Task` (`execute` → POST `ExecuteTask`), `CalculationRegister` (`schedule_data` / `actual_action_period` → `ScheduledData` / `ActualActionPeriod`), `ChartOfCharacteristicTypes`, `ChartOfCalculationTypes`.
- `Infobase.entity_sets()` and `has_entity_set()` parse EntitySet names from `$metadata` (cached). No typed-class codegen.
- Filter helpers `isof()` and `cast()` emit OData 3.0 text (`isof(Field, 'Edm.String')`).

## [0.3.0] - 2026-09-02

### Added

- Filter DSL: `F("Цена") > 1000`, `&` / `|` / `~`, and `startswith` / `endswith` / `substringof` / `contains`.
- `Query` builder (`where` / `build`) on every entity set. `query(odata_filter=str)` still works.
- `Page` wrapper for collection responses (`value`, `count` from `$inlinecount`).
- `EntitySet.iterate()` pages with `$top` / `$skip` until a short or empty page.
- `EntitySet.count()` via `$top=0&$inlinecount=allpages`.
- `Infobase(debug=True)` or `debug=callable`: method, decoded URL, status, milliseconds. Authorization is not logged. `last_url` / `last_status` on the client.
- Typed errors: `EntityNotFound` (404), `AccessDenied` (403), `ConcurrencyError` (412), still subclasses of `ODataError`.
- `if_match=` on `edit` / `replace` / `delete` sends `If-Match` (1C `DataVersion`).
- Entity types: `AccountingRegister` (Balance / Turnovers / BalanceAndTurnovers), `ChartOfAccounts`, `DocumentJournal` (query/get), `Constant`, `ExchangePlan`.

### Changed

- `EntitySet.query()` returns a `Page` (still mapping-compatible with the raw JSON).
- Package version 0.3.0. CI runs ruff and mypy in addition to pytest.

## [0.2.1] - 2026-08-24

### Added

- RLS `allowedOnly`, `$inlinecount`, `$metadata`, composite keys, GitHub Actions.

## [0.1.2] - 2025-05-15

Initial PyPI release of the async 1C OData client.

[0.4.0]: https://github.com/itsuppartem/python_1c_odata/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/itsuppartem/python_1c_odata/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/itsuppartem/python_1c_odata/compare/v0.1.2...v0.2.1
[0.1.2]: https://github.com/itsuppartem/python_1c_odata/releases/tag/v0.1.2
