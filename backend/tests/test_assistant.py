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


# Questions the tester asked that used to get the same summary every time.
MORE_QUESTIONS: list[tuple[str, str, set[str]]] = [
    ("Kakva je okolina?", "overview", set()),
    ("Je li ovo dobro mjesto za obitelj s djecom?", "overview", set()),
    ("Gdje je najbliža bolnica?", "no_data", set()),
    ("Je li sigurno za život?", "no_data", set()),
    ("Je li sigurno od poplava?", "report", {"flood"}),
    ("Ima li ovdje optički internet?", "no_data", set()),
    ("Gdje je najbliža srednja škola?", "no_data", {"school"}),
    ("Koliko ima stanovnika?", "report", set()),
    ("Je li ulica tiha?", "report", {"noise"}),
    ("Što mislite o ovome?", "unknown", set()),
]


@pytest.mark.parametrize(("question", "intent", "categories"), MORE_QUESTIONS)
def test_rules_tell_general_unknown_and_missing_topics_apart(
    question: str, intent: str, categories: set[str]
) -> None:
    understood = understand_rules(question)
    assert understood.intent == intent
    assert categories <= set(understood.categories)


def _ask(question: str) -> tuple[str, int]:
    built: list[int] = []

    def build(lat: float, lon: float, label: str | None) -> Report:
        built.append(1)
        report = _report(12.3, "X")
        report.location.settlement = "Split"
        report.location.population = Value(
            key="settlement_population",
            label="Stanovnika u naselju Split",
            value=149830,
            unit="stanovnika",
            display="149.830 stanovnika (Popis 2021.)",
            source="dzs_popis",
            retrieved_at=None,
            kind="measured",
        )
        return report

    request = AssistantRequest(question=question, locations=[AssistantLocation(lat=45.0, lon=16.0)])
    return answer(request, build).answer, len(built)


def test_unknown_question_says_so_and_lists_topics() -> None:
    text, built = _ask("Što mislite o ovome?")
    assert text.startswith("Ovo pitanje ne razumijem.")
    assert "poplave" in text and "Sažetak." not in text
    assert built == 0


def test_missing_topic_is_named_without_building_a_report() -> None:
    text, built = _ask("Gdje je najbliža bolnica?")
    assert text.startswith("O bolnicama i hitnoj pomoći nemamo podatke.")
    assert built == 0


def test_general_question_gets_the_summary() -> None:
    text, _ = _ask("Kakva je okolina?")
    assert "Sažetak." in text


def test_population_comes_from_the_report() -> None:
    text, _ = _ask("Koliko ima stanovnika?")
    assert "naselje Split ima 149.830 stanovnika (Popis 2021.)" in text


def test_different_questions_get_different_answers() -> None:
    questions = [
        "Kakav je zrak?",
        "Kakva je okolina?",
        "Gdje je najbliža bolnica?",
        "Koliko ima stanovnika?",
        "Što mislite o ovome?",
    ]
    answers = {_ask(q)[0] for q in questions}
    assert len(answers) == len(questions)
