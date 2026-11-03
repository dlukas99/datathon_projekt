"""Category status labels shown to people."""

from __future__ import annotations

from app.models import Status

STATUS_LABELS: dict[Status, str] = {
    "good": "Dobro",
    "warning": "Upozorenje",
    "bad": "Loše",
    "no_data": "Nema podataka",
    "info": "Informacija",
}


def label(status: Status) -> str:
    return STATUS_LABELS[status]
