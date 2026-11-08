"""Number formatting in the hr-HR convention (1.234,5)."""

from __future__ import annotations


def num(value: float, decimals: int = 0) -> str:
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def minutes_word(n: int) -> str:
    """1 minuta, 2 minute, 5 minuta, 21 minuta, 22 minute."""
    return f"{num(n)} {plural(n, 'minuta', 'minute', 'minuta')}"


def minutes(value: float | None) -> str:
    """Walking time in words: "manje od minute", "1 minuta", "4 minute", "12 minuta"."""
    if value is None:
        return "nije izračunato"
    if value < 1:
        return "manje od minute"
    return minutes_word(round(value))


def metres(value: float | None) -> str:
    if value is None:
        return "nepoznato"
    rounded = round(value / 10) * 10
    if rounded >= 1000:
        return f"{num(value / 1000, 1)} km"
    return f"{num(rounded)} m"


def plural(n: int, one: str, few: str, many: str) -> str:
    """Croatian plural form: 1 park, 2 parka, 5 parkova."""
    if n % 10 == 1 and n % 100 != 11:
        return one
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return few
    return many
