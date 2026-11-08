"""Assistant: keyword rules (no language model), several topics per message, follow-ups."""

import pytest

from app.assistant import (
    DISCLAIMER,
    AssistantLocation,
    AssistantReply,
    AssistantRequest,
    _comparison,
    _readable,
    answer,
    fmt_decimal,
    fmt_int,
    fmt_metres,
    fmt_minutes,
    understand_rules,
)
from app.models import Category, Location, Place, Report, Value


def topics(question: str, context: tuple[str, ...] = ()) -> list[tuple[str, str]]:
    return [(p.kind, p.topic) for p in understand_rules(question, context)]


def cats(question: str, context: tuple[str, ...] = ()) -> list[str]:
    return [t for k, t in topics(question, context) if k == "category"]


# The questions of docs/ASISTENT.md: (question, part kind, categories that must be found).
QUESTIONS: list[tuple[str, str, set[str]]] = [
    ("Je li ova kuća u poplavnom području?", "category", {"flood"}),
    ("Može li se ovdje izliti rijeka?", "category", {"flood"}),
    ("Kakav je zrak na ovoj adresi?", "category", {"air"}),
    ("Ima li puno prašine i smoga?", "category", {"air"}),
    ("Ima li dovoljno drveća i hlada ljeti?", "category", {"green"}),
    ("Koliko je daleko najbliži park?", "category", {"green"}),
    ("Je li bučno zbog prometa?", "category", {"noise"}),
    ("Isplate li se solarni paneli na krovu?", "category", {"solar"}),
    ("Mogu li ovdje živjeti bez auta?", "category", {"car_free"}),
    ("Ima li autobus ili tramvaj u blizini?", "category", {"transit"}),
    ("Koliko je daleko vrtić?", "category", {"kindergarten"}),
    ("Gdje je najbliža osnovna škola?", "category", {"school"}),
    ("Ima li obiteljski liječnik u blizini?", "category", {"doctor"}),
    ("Gdje je najbliži pedijatar?", "category", {"pediatrician"}),
    ("Koliko je do ljekarne?", "category", {"pharmacy"}),
    ("Ima li trgovina namirnicama blizu?", "category", {"grocery"}),
    ("Što znači povratno razdoblje poplave?", "explain", {"flood"}),
    ("Trebam li kupiti ovu kuću?", "purchase", set()),
    ("Koliko košta kvadrat u ovoj ulici?", "scope", set()),
    ("Je li zemljišnoknjižno stanje uredno?", "scope", set()),
    ("Kakva je okolina?", "overview", set()),
    ("Je li ovo dobro mjesto za obitelj s djecom?", "overview", set()),
    ("Gdje je najbliža bolnica?", "gap", set()),
    ("Je li sigurno za život?", "gap", set()),
    ("Je li sigurno od poplava?", "category", {"flood"}),
    ("Ima li ovdje optički internet?", "gap", set()),
    ("Gdje je najbliža srednja škola?", "gap", {"school"}),
    ("Koliko ima stanovnika?", "population", set()),
    ("Je li ulica tiha?", "category", {"noise"}),
    ("Koje su glavne prednosti i mane ove lokacije?", "pros_cons", set()),
    ("Što je najbliže?", "nearby", set()),
    ("Što je u krugu 10 minuta?", "nearby", set()),
    ("Što ne znaš?", "limits", set()),
    ("Što nije provjereno?", "limits", set()),
]


@pytest.mark.parametrize(("question", "kind", "categories"), QUESTIONS)
def test_rules_understand_question(question: str, kind: str, categories: set[str]) -> None:
    found = topics(question)
    assert kind in {k for k, _ in found}
    assert categories <= {t for _, t in found}


def test_unrelated_question_is_not_understood() -> None:
    assert topics("Što mislite o ovome?") == []


def test_several_topics_in_one_message_in_the_order_asked() -> None:
    assert cats("Kakav je zrak, ima li vrtić i koliko je do ljekarne?") == [
        "air",
        "kindergarten",
        "pharmacy",
    ]
    assert cats("Ima li ljekarna blizu i kakav je zrak?") == ["pharmacy", "air"]


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("ima li skola blizu", ["school"]),
        ("gdje je ljecnik", ["doctor"]),
        ("koliko je do vrtica", ["kindergarten"]),
        ("Kakva je kvaliteta zraka?", ["air"]),
        ("Što je sa zrakom u zimi?", ["air"]),
        ("Ima li ljekarni u blizini?", ["pharmacy"]),
        ("Gdje je najbliža apoteka?", ["pharmacy"]),
        ("Ima li doktor opće prakse?", ["doctor"]),
        ("Vozi li bus?", ["transit"]),
        ("Ima li zelenih površina?", ["green"]),
        ("Ima li parking?", []),
    ],
)
def test_without_diacritics_cases_and_synonyms(question: str, expected: list[str]) -> None:
    assert cats(question) == expected


def test_follow_up_uses_the_previous_topics() -> None:
    assert cats("A škola?", ("kindergarten",)) == ["school"]
    parts = understand_rules("A pješice?", ("kindergarten",))
    assert [(p.topic, p.walking) for p in parts] == [("kindergarten", True)]
    # Without a conversation "pješice" is about life without a car.
    assert cats("A pješice?") == ["car_free"]
    assert topics("Zašto?", ("flood",)) == [("explain", "flood")]


def test_walking_to_a_place_is_not_life_without_a_car() -> None:
    assert cats("Koliko je pješice do vrtića?") == ["kindergarten"]


def test_part_not_covered_is_kept_next_to_the_answer() -> None:
    found = understand_rules("Kakav je zrak i ima li u blizini pikado klub?")
    assert [p.kind for p in found] == ["category", "uncovered"]
    assert found[1].clause == "ima li u blizini pikado klub"


# --- numbers -------------------------------------------------------------------------


def test_croatian_number_formats() -> None:
    assert fmt_int(28111) == "28.111"
    assert fmt_int(950) == "950"
    assert fmt_decimal(9.94) == "9,9"
    assert fmt_decimal(10.0) == "10"
    assert fmt_minutes(6.6) == "7 min"
    assert fmt_minutes(0.2) == "1 min"
    assert fmt_metres(373) == "370 m"
    assert fmt_metres(1360) == "1,4 km"
    assert fmt_metres(2000) == "2 km"
    assert _readable("18,2 µg/m³ (umjerena razina)") == "18,2 µg/m³ – umjerena razina"
    assert _readable("7 %") == "7 %"


# --- answers over a report -----------------------------------------------------------


def _value(key: str, label: str, value: float | str, unit: str | None, display: str) -> Value:
    return Value(
        key=key,
        label=label,
        value=value,
        unit=unit,
        display=display,
        source="eea_pm25",
        retrieved_at="2026-11-05T19:54:11+00:00",
        kind="modelled",
    )


def _report(pm25: float = 12.3, label: str = "X") -> Report:
    air = Category(
        id="air",
        group="environment",
        title="Kvaliteta zraka",
        status="good",
        status_label="Dobar",
        headline="Kroz godinu je zrak ovdje malo onečišćen.",
        values=[
            _value(
                "pm25_annual",
                "PM2,5, godišnji prosjek 2024.",
                pm25,
                "µg/m³",
                f"{fmt_decimal(pm25)} µg/m³ (niska razina)",
            )
        ],
        notes=["Karta EEA-e procjena je godišnjeg prosjeka na mreži od 1 km."],
    )
    green = Category(
        id="green",
        group="environment",
        title="Zelenilo i hlad",
        status="warning",
        status_label="Upozorenje",
        headline="Drveće pokriva 7 % kopna u krugu od 300 m.",
        values=[_value("tree_share_300m", "Udio drveća u krugu od 300 m", 7.5, "%", "7 %")],
    )
    flood = Category(
        id="flood",
        group="environment",
        title="Poplave",
        status="good",
        status_label="Dobro",
        headline="Lokacija nije u modeliranom području riječnih poplava.",
    )
    daily = Category(
        id="daily",
        group="daily",
        title="Svakodnevni život",
        status="info",
        status_label="Informacija",
        headline="Predložak.",
        values=[
            _value("nearest_pharmacy", "Ljekarna", 4.9, "min", "5 min hoda (Ljekarna Centar)"),
            _value("count15_pharmacy", "Ljekarna: broj unutar 15 minuta hoda", 3, None, "3"),
            _value("nearest_school", "Osnovna škola", 21.0, "min", "21 min hoda (OŠ Jug)"),
        ],
        places=[
            Place(
                category="pharmacy",
                name="Ljekarna Centar",
                lat=45.001,
                lon=16.001,
                walk_minutes=4.9,
                distance_m=283,
                source="hzzo_ljekarne",
                retrieved_at=None,
                kind="modelled",
            )
        ],
    )
    return Report(
        location=Location(lat=45.0, lon=16.0, label=label, settlement="Split"),
        generated_at="2026-11-02T00:00:00+00:00",
        summary=["Sažetak izvještaja."],
        categories=[air, green, flood, daily],
        sources=[],
        disclaimer="",
    )


def _ask(question: str, context: list[str] | None = None) -> tuple[AssistantReply, int]:
    built: list[int] = []

    def build(lat: float, lon: float, label: str | None) -> Report:
        built.append(1)
        return _report()

    request = AssistantRequest(
        question=question,
        locations=[AssistantLocation(lat=45.0, lon=16.0)],
        context=context or [],
    )
    return answer(request, build), len(built)


def test_comparison_names_lower_concentration() -> None:
    sentence = _comparison([_report(17.8, "A"), _report(9.7, "B")], "air")
    assert sentence == "Nižu godišnju koncentraciju PM2,5 ima adresa B."


def test_block_has_natural_text_lines_and_sources_apart() -> None:
    reply, _ = _ask("Kakav je zrak?")
    block = reply.blocks[0]
    assert block.title == "Kvaliteta zraka"
    assert (block.status, block.status_label) == ("good", "Dobar")
    assert block.text.startswith("Kroz godinu je zrak ovdje malo onečišćen.")
    assert "Za ovu adresu" not in block.text
    assert [(line.label, line.value) for line in block.lines] == [
        ("PM2,5", "12,3 µg/m³ – niska razina")
    ]
    assert block.sources[0].kind == "modelled"
    assert block.method == ["Karta EEA-e procjena je godišnjeg prosjeka na mreži od 1 km."]
    assert DISCLAIMER not in reply.answer
    assert reply.topics == ["air"]
    assert "A buka i promet?" in reply.suggestions


def test_several_topics_get_a_block_each_and_a_summary() -> None:
    reply, built = _ask("Kakav je zrak, ima li ljekarna blizu i kakvo je zelenilo?")
    assert [b.topic for b in reply.blocks] == ["air", "pharmacy", "green"]
    assert built == 1
    assert (
        reply.summary == "Ukratko: dobro stoje kvaliteta zraka i ljekarna; slabije zelenilo i hlad."
    )


def test_yes_no_question_starts_with_the_answer() -> None:
    reply, _ = _ask("Ima li ljekarna blizu?")
    block = reply.blocks[0]
    assert block.text == "Da – najbliža ljekarna je 5 min hoda od adrese."
    assert [(line.label, line.value) for line in block.lines] == [
        ("Najbliže", "Ljekarna Centar"),
        ("Pješice", "5 min hoda (zračno 280 m)"),
        ("Unutar 15 min hoda", "3"),
    ]
    reply, _ = _ask("Ima li škola blizu?")
    assert reply.blocks[0].text.startswith("Ne unutar 15 minuta hoda – najbliža osnovna škola")


def test_follow_up_answer_uses_the_context() -> None:
    reply, _ = _ask("A pješice?", context=["pharmacy"])
    assert reply.blocks[0].topic == "pharmacy"
    assert "zračnom linijom 280 m" in reply.blocks[0].text


def test_partly_covered_question_answers_the_rest_and_says_what_is_missing() -> None:
    reply, _ = _ask("Kakav je zrak i ima li u blizini pikado klub?")
    assert [b.topic for b in reply.blocks] == ["air", "uncovered"]
    missing = reply.blocks[1]
    assert missing.status == "no_data"
    assert missing.text == "Za „pikado klub” nemamo podatke, pa to ne mogu procijeniti."


def test_purchase_advice_is_refused_but_the_facts_are_given() -> None:
    reply, _ = _ask("Isplati li se kupiti i kakav je zrak?")
    assert [b.topic for b in reply.blocks] == ["purchase", "air"]
    assert reply.blocks[0].text.startswith("Ne dajem savjete")


def test_unknown_question_says_so_and_suggests_questions() -> None:
    reply, built = _ask("Što mislite o ovome?")
    assert reply.blocks[0].topic == "unknown"
    assert reply.answer.startswith("To pitanje ne mogu povezati s podacima za ovu adresu.")
    assert len(reply.suggestions) == 3
    assert built == 0


def test_missing_topic_is_named_without_building_a_report() -> None:
    reply, built = _ask("Gdje je najbliža bolnica?")
    assert reply.blocks[0].text.startswith("O bolnicama i hitnoj pomoći nemamo podatke.")
    assert reply.blocks[0].status == "no_data"
    assert built == 0


def test_general_question_gets_the_summary_and_the_strengths() -> None:
    reply, _ = _ask("Kakva je okolina?")
    block = reply.blocks[0]
    assert block.text == "Sažetak izvještaja."
    assert [(c.label, c.tone) for c in block.chips] == [
        ("Kvaliteta zraka · dobar", "good"),
        ("Poplave · dobro", "good"),
        ("Zelenilo i hlad · upozorenje", "missing"),
        ("Osnovna škola · 21 min hoda", "missing"),
    ]


def test_pros_and_cons_are_not_purchase_advice() -> None:
    reply, _ = _ask("Koje su prednosti i mane?")
    assert reply.blocks[0].text == (
        "Dobro ocijenjeno: kvaliteta zraka i poplave. Slabije: zelenilo i hlad te osnovna "
        "škola. Ovo je pregled kategorija iz izvještaja, a ne savjet o kupnji."
    )


def test_nearby_lists_places_within_the_minutes_asked() -> None:
    reply, _ = _ask("Što je u krugu 10 minuta?")
    block = reply.blocks[0]
    assert block.text == "Unutar 10 minuta hoda je 1 od 2 vrsta mjesta koje pratimo."
    assert [(c.label, c.tone) for c in block.chips] == [
        ("Ljekarna · 5 min", "good"),
        ("Osnovna škola · 21 min", "missing"),
    ]


def test_population_comes_from_the_report() -> None:
    def build(lat: float, lon: float, label: str | None) -> Report:
        report = _report()
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

    request = AssistantRequest(
        question="Koliko ima stanovnika?", locations=[AssistantLocation(lat=45.0, lon=16.0)]
    )
    reply = answer(request, build)
    assert reply.blocks[0].text == "U naselju Split prema Popisu 2021. živi 149.830 stanovnika."


def test_different_questions_get_different_answers() -> None:
    questions = [
        "Kakav je zrak?",
        "Kakva je okolina?",
        "Gdje je najbliža bolnica?",
        "Ima li ljekarna blizu?",
        "Što mislite o ovome?",
        "Što ne znaš?",
    ]
    answers = {_ask(q)[0].answer for q in questions}
    assert len(answers) == len(questions)
