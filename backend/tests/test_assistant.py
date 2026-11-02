"""The 20 test questions from docs/ASISTENT.md (keyword rules, no language model)."""

import pytest

from app.assistant import (
    AssistantLocation,
    AssistantRequest,
    _comparison,
    answer,
    understand_rules,
)
from app.models import Category, Location, Report, Value

QUESTIONS: list[tuple[str, str, set[str]]] = [
    ("Je li ova kuća u poplavnom području?", "report", {"flood"}),
    ("Može li se ovdje izliti rijeka?", "report", {"flood"}),
    ("Kakav je zrak na ovoj adresi?", "report", {"air"}),
    ("Ima li puno prašine i smoga?", "report", {"air"}),
    ("Ima li dovoljno drveća i hlada ljeti?", "report", {"green"}),
    ("Koliko je daleko najbliži park?", "report", {"green"}),
    ("Je li bučno zbog prometa?", "report", {"noise"}),
    ("Isplate li se solarni paneli na krovu?", "report", {"solar"}),
    ("Mogu li ovdje živjeti bez auta?", "report", {"car_free"}),
    ("Ima li autobus ili tramvaj u blizini?", "report", {"transit"}),
    ("Koliko je daleko vrtić?", "report", {"kindergarten"}),
    ("Gdje je najbliža osnovna škola?", "report", {"school"}),
    ("Ima li obiteljski liječnik u blizini?", "report", {"doctor"}),
    ("Gdje je najbliži pedijatar?", "report", {"pediatrician"}),
    ("Koliko je do ljekarne?", "report", {"pharmacy"}),
    ("Ima li trgovina namirnicama blizu?", "report", {"grocery"}),
    ("Što znači povratno razdoblje poplave?", "explain", {"flood"}),
    ("Trebam li kupiti ovu kuću?", "purchase_advice", set()),
    ("Koliko košta kvadrat u ovoj ulici?", "out_of_scope", set()),
    ("Je li zemljišnoknjižno stanje uredno?", "out_of_scope", set()),
]


@pytest.mark.parametrize(("question", "intent", "categories"), QUESTIONS)
def test_rules_understand_question(question: str, intent: str, categories: set[str]) -> None:
    understood = understand_rules(question)
    assert understood.intent == intent
    assert categories <= set(understood.categories)


def _report(pm25: float, label: str) -> Report:
    air = Category(
        id="air",
        group="environment",
        title="Kvaliteta zraka",
        status="bad",
        status_label="Loše",
        headline="Predložak.",
        values=[
            Value(
                key="pm25_annual",
                label="PM2,5",
                value=pm25,
                unit="µg/m³",
                display=f"{pm25} µg/m³",
                source="eea_pm25",
                retrieved_at=None,
                kind="modelled",
            )
        ],
    )
    return Report(
        location=Location(lat=45.0, lon=16.0, label=label),
        generated_at="2026-11-02T00:00:00+00:00",
        summary=["Sažetak."],
        categories=[air],
        sources=[],
        disclaimer="",
    )


def test_comparison_names_lower_concentration() -> None:
    sentence = _comparison([_report(17.8, "A"), _report(9.7, "B")], "air")
    assert sentence == "Nižu godišnju koncentraciju PM2,5 ima adresa B."


def test_answer_uses_only_report_values() -> None:
    request = AssistantRequest(
        question="Kakav je zrak?", locations=[AssistantLocation(lat=45.0, lon=16.0)]
    )
    reply = answer(request, lambda lat, lon, label: _report(12.3, "X"))
    assert reply.mode == "rules"
    assert "Predložak." in reply.answer
    assert reply.facts[0].text == "PM2,5: 12.3 µg/m³"


def test_purchase_advice_is_refused() -> None:
    request = AssistantRequest(
        question="Vrijedi li kupiti ovaj stan?", locations=[AssistantLocation(lat=45.0, lon=16.0)]
    )
    reply = answer(request, lambda lat, lon, label: _report(1.0, "X"))
    assert reply.answer.startswith("Ne dajem savjete")
