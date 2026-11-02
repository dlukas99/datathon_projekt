"""Rooftop solar potential from JRC PVGIS."""

from __future__ import annotations

from analysis.status import label
from app import fmt, pvgis
from app.models import Category, Link, Value

PVGIS_TOOL = "https://re.jrc.ec.europa.eu/pvg_tools/en/"


def solar_category(lat: float, lon: float) -> Category:
    try:
        result = pvgis.yearly_output(lat, lon)
    except pvgis.SolarUnavailable:
        return Category(
            id="solar",
            group="environment",
            title="Sunce na krovu",
            status="no_data",
            status_label=label("no_data"),
            headline="Servis PVGIS trenutačno nije dostupan, pa procjenu nije moguće prikazati.",
            links=[Link(label="PVGIS (JRC)", url=PVGIS_TOOL)],
        )
    kwh = result.kwh_per_kwp_year
    return Category(
        id="solar",
        group="environment",
        title="Sunce na krovu",
        status="info",
        status_label=label("info"),
        headline=(
            f"Fotonaponska elektrana snage 1 kW ovdje bi godišnje proizvela oko "
            f"{fmt.num(kwh)} kWh, uz optimalni nagib od {fmt.num(result.optimal_slope_deg)}°."
        ),
        values=[
            Value(
                key="pv_kwh_per_kwp",
                label="Godišnja proizvodnja po kW snage",
                value=round(kwh, 1),
                unit="kWh/kWp",
                display=f"{fmt.num(kwh)} kWh godišnje",
                source="pvgis",
                retrieved_at=result.retrieved_at,
                kind="modelled",
                note=(
                    f"Model PVGIS, podaci o zračenju {result.radiation_db} za razdoblje "
                    f"{result.years}, gubici sustava {pvgis.SYSTEM_LOSS_PCT} %."
                ),
            ),
            Value(
                key="pv_optimal_slope",
                label="Optimalni nagib panela",
                value=result.optimal_slope_deg,
                unit="°",
                display=f"{fmt.num(result.optimal_slope_deg)}°",
                source="pvgis",
                retrieved_at=result.retrieved_at,
                kind="modelled",
            ),
        ],
        notes=[
            "Procjena ne uzima u obzir sjenu susjednih zgrada i drveća ni stvarni nagib "
            "i orijentaciju vašeg krova.",
        ],
        links=[Link(label="Detaljan izračun u alatu PVGIS (JRC)", url=PVGIS_TOOL)],
    )
