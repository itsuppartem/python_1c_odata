"""OData 3.0 $filter expressions for 1C (guid/datetime literals, not v4)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from python_1c_odata.literals import guid, odata_datetime


class Filter:
    """Boolean OData 3.0 expression. Combine with ``&``, ``|``, ``~`` (parenthesize comparisons)."""

    def __init__(self, text: str) -> None:
        self.text = text

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"Filter({self.text!r})"

    def __eq__(self, other: object) -> Filter:  # type: ignore[override]
        return Filter(f"{self.text} eq {_literal(other)}")

    def __ne__(self, other: object) -> Filter:  # type: ignore[override]
        return Filter(f"{self.text} ne {_literal(other)}")

    def __gt__(self, other: object) -> Filter:
        return Filter(f"{self.text} gt {_literal(other)}")

    def __ge__(self, other: object) -> Filter:
        return Filter(f"{self.text} ge {_literal(other)}")

    def __lt__(self, other: object) -> Filter:
        return Filter(f"{self.text} lt {_literal(other)}")

    def __le__(self, other: object) -> Filter:
        return Filter(f"{self.text} le {_literal(other)}")

    def __and__(self, other: object) -> Filter:
        return Filter(f"({self.text}) and ({_operand(other)})")

    def __or__(self, other: object) -> Filter:
        return Filter(f"({self.text}) or ({_operand(other)})")

    def __rand__(self, other: object) -> Filter:
        return Filter(f"({_operand(other)}) and ({self.text})")

    def __ror__(self, other: object) -> Filter:
        return Filter(f"({_operand(other)}) or ({self.text})")

    def __invert__(self) -> Filter:
        return Filter(f"not ({self.text})")

    def eq(self, other: object) -> Filter:
        return self == other

    def ne(self, other: object) -> Filter:
        return self != other

    def gt(self, other: object) -> Filter:
        return self > other

    def ge(self, other: object) -> Filter:
        return self >= other

    def lt(self, other: object) -> Filter:
        return self < other

    def le(self, other: object) -> Filter:
        return self <= other

    def and_(self, other: object) -> Filter:
        return self & other

    def or_(self, other: object) -> Filter:
        return self | other

    def startswith(self, value: object) -> Filter:
        return startswith(self, value)

    def endswith(self, value: object) -> Filter:
        return endswith(self, value)

    def contains(self, value: object) -> Filter:
        return contains(self, value)

    def substringof(self, needle: object) -> Filter:
        return substringof(needle, self)

    def isof(self, type_name: str) -> Filter:
        return isof(self, type_name)

    def cast(self, type_name: str) -> Filter:
        return cast(self, type_name)

    def any(self, predicate: str | Filter) -> Filter:
        """OData 3.0: ``Товары/any(d: d/Цена gt 10000)``."""
        return Filter(f"{self.text}/any(d: {_lambda_body(predicate)})")

    def all(self, predicate: str | Filter) -> Filter:
        """OData 3.0: ``Товары/all(d: d/Цена gt 10000)``."""
        return Filter(f"{self.text}/all(d: {_lambda_body(predicate)})")


class F(Filter):
    """Field reference: ``F("Цена") > 1000``, ``F("Ref_Key") == guid("...")``."""

    def __init__(self, name: str) -> None:
        super().__init__(name)


def startswith(field: str | Filter, value: object) -> Filter:
    return Filter(f"startswith({_field(field)}, {_literal(value)})")


def endswith(field: str | Filter, value: object) -> Filter:
    return Filter(f"endswith({_field(field)}, {_literal(value)})")


def substringof(needle: object, haystack: str | Filter) -> Filter:
    """OData 3.0: ``substringof(needle, haystack)``."""
    return Filter(f"substringof({_literal(needle)}, {_field(haystack)})")


def contains(haystack: str | Filter, needle: object) -> Filter:
    """OData 3.0 spelling of contains: ``substringof(needle, haystack)``."""
    return substringof(needle, haystack)


def isof(field: str | Filter, type_name: str) -> Filter:
    """OData 3.0: ``isof(Field, 'Edm.String')``."""
    return Filter(f"isof({_field(field)}, {_type_name(type_name)})")


def cast(field: str | Filter, type_name: str) -> Filter:
    """OData 3.0: ``cast(Field, 'Edm.String')``."""
    return Filter(f"cast({_field(field)}, {_type_name(type_name)})")


def any_(collection: str | Filter, predicate: str | Filter) -> Filter:
    """Module-level ``any`` (named ``any_`` so the builtin is not shadowed)."""
    return F(_field(collection)).any(predicate)


def all_(collection: str | Filter, predicate: str | Filter) -> Filter:
    """Module-level ``all`` (named ``all_`` so the builtin is not shadowed)."""
    return F(_field(collection)).all(predicate)


def as_filter_text(odata_filter: str | Filter | None) -> str | None:
    if odata_filter is None:
        return None
    return str(odata_filter)


_LAMBDA_VAR = "d"
_RESERVED = frozenset(
    {
        "eq",
        "ne",
        "gt",
        "ge",
        "lt",
        "le",
        "and",
        "or",
        "not",
        "true",
        "false",
        "null",
        "startswith",
        "endswith",
        "substringof",
        "contains",
        "isof",
        "cast",
        "any",
        "all",
        "guid",
        "datetime",
        "edm",
    }
)


def _lambda_body(predicate: str | Filter) -> str:
    return _prefix_lambda_fields(str(predicate), _LAMBDA_VAR)


def _prefix_lambda_fields(text: str, var: str) -> str:
    """Prefix bare field names with ``d/``; leave operators, literals, and paths alone."""
    out: list[str] = []
    i = 0
    n = len(text)
    last_significant = ""
    while i < n:
        ch = text[i]
        if ch == "'":
            j = i + 1
            while j < n:
                if text[j] == "'":
                    if j + 1 < n and text[j + 1] == "'":
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            token = text[i:j]
            out.append(token)
            last_significant = token
            i = j
            continue
        if ch.isalpha() or ch == "_":
            j = i + 1
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            ident = text[i:j]
            if (
                ident.lower() in _RESERVED
                or ident == var
                or last_significant.endswith("/")
                or last_significant == "."
            ):
                out.append(ident)
            else:
                out.append(f"{var}/{ident}")
            last_significant = ident
            i = j
            continue
        out.append(ch)
        if not ch.isspace():
            last_significant = ch
        i += 1
    return "".join(out)


def _field(value: str | Filter) -> str:
    return value.text if isinstance(value, Filter) else value


def _type_name(type_name: str) -> str:
    if type_name.startswith("'") and type_name.endswith("'"):
        return type_name
    return "'" + type_name.replace("'", "''") + "'"


def _operand(value: object) -> str:
    if isinstance(value, Filter):
        return value.text
    return _literal(value)


def _literal(value: object) -> str:
    if isinstance(value, Filter):
        return value.text
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, UUID):
        return guid(str(value))
    if isinstance(value, (datetime, date)):
        return odata_datetime(value)
    if isinstance(value, str):
        if value.startswith(("guid'", "datetime'")):
            return value
        return "'" + value.replace("'", "''") + "'"
    raise TypeError(f"unsupported filter literal: {value!r}")
