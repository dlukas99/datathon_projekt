"""Can machine learning improve the annual PM2.5/NO2 estimate at street level?

Target: 2024 annual mean at official stations (ingest/stations.py).
Baseline: the EEA 1 km map value at the station (what the app shows).
Models predict the station value from the EEA value plus local features that
the app also knows for any address:
  distance to a major road, built-up and tree share within 300 m (WorldCover),
  log population of the settlement.
Evaluation: leave-one-station-out cross-validation (each station is predicted
by a model that never saw it). Decision rule, fixed in advance: a model enters
the app only if its LOSO RMSE is lower than the baseline for both pollutants.

    uv run python -m analysis.ml_air      (prints a Markdown report)
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from shapely.geometry import Point
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

from analysis.environment import read_air, read_landcover
from app.admin import get_admin
from app.config import get_settings
from app.geo import to_htrs
from app.layers import get_layers

FEATURES = ["eea", "road_m", "built", "tree", "log_pop"]


def features(lon: float, lat: float, pollutant: str) -> dict[str, float]:
    layers = get_layers()
    lines = layers.noise_lines
    road = 2000.0
    if lines is not None:
        x, y = to_htrs(lon, lat)
        origin = Point(x, y)
        for i in lines.tree.query(origin.buffer(2000.0), predicate="intersects"):
            if lines.kinds[int(i)] != "rail":
                road = min(road, float(lines.geoms[int(i)].distance(origin)))
    cover = read_landcover(lon, lat) or {"built": math.nan, "tree": math.nan}
    admin = get_admin()
    place = admin.lookup(lon, lat) if admin else None
    pop = place.population if place and place.population else 1
    eea = read_air(lon, lat, pollutant)
    return {
        "eea": math.nan if eea is None else eea,
        "road_m": road,
        "built": cover["built"],
        "tree": cover["tree"],
        "log_pop": math.log10(pop),
    }


def dataset() -> pd.DataFrame:
    st = pd.read_parquet(get_settings().processed_dir / "stations_2024.parquet")
    st = st[st["mean"].notna()]
    rows = []
    for r in st.to_dict("records"):
        f = features(float(r["lon"]), float(r["lat"]), str(r["pollutant"]))
        rows.append(
            {
                "station": r["station_name"],
                "type": r["type"],
                "pollutant": r["pollutant"],
                "y": float(r["mean"]),
                **f,
            }
        )
    return pd.DataFrame(rows).dropna()


@dataclass
class Scores:
    rmse: float
    mae: float
    bias: float


def _scores(y: NDArray[np.float64], p: NDArray[np.float64]) -> Scores:
    e = p - y
    return Scores(float(np.sqrt(np.mean(e**2))), float(np.mean(np.abs(e))), float(np.mean(e)))


def loso(df: pd.DataFrame) -> dict[str, Scores]:
    y = df["y"].to_numpy(float)
    X = df[FEATURES].to_numpy(float)
    eea = df["eea"].to_numpy(float)
    preds: dict[str, list[float]] = {
        "EEA karta (osnova)": [],
        "EEA + prosječno odstupanje": [],
        "Linearna regresija": [],
        "Random Forest": [],
    }
    for i in range(len(df)):
        train = np.arange(len(df)) != i
        resid = y[train] - eea[train]
        preds["EEA karta (osnova)"].append(eea[i])
        preds["EEA + prosječno odstupanje"].append(eea[i] + resid.mean())
        lin = LinearRegression().fit(X[train], resid)
        preds["Linearna regresija"].append(eea[i] + float(lin.predict(X[i : i + 1])[0]))
        rf = RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=0)
        rf.fit(X[train], resid)
        preds["Random Forest"].append(eea[i] + float(rf.predict(X[i : i + 1])[0]))
    return {k: _scores(y, np.array(v)) for k, v in preds.items()}


def report() -> str:
    df = dataset()
    out = ["| Tvar | Postaja (n) | Model | RMSE | MAE | Pristranost |", "|---|---|---|---|---|---|"]
    verdicts = []
    for pol, name in (("pm25", "PM2,5"), ("no2", "NO2")):
        part = df[df["pollutant"] == pol].reset_index(drop=True)
        res = loso(part)
        base = res["EEA karta (osnova)"].rmse
        for model, s in res.items():
            row = f"| {name} | {len(part)} | {model} | {s.rmse:.2f} | {s.mae:.2f} | {s.bias:+.2f} |"
            out.append(row.replace(".", ","))
        rf = res["Random Forest"].rmse
        verdicts.append((name, base, rf))
    out.append("")
    for name, base, rf in verdicts:
        change = (rf - base) / base * 100
        line = f"- {name}: RMSE osnove {base:.2f}, Random Forest {rf:.2f} µg/m³ ({change:+.0f} %)."
        out.append(line.replace(".", ",", 2))
    better = all(rf < base for _, base, rf in verdicts)
    out.append("")
    out.append(
        "**Odluka:** model "
        + (
            "ulazi u aplikaciju."
            if better
            else "ne ulazi u aplikaciju; ostaje vrijednost EEA karte."
        )
    )
    return "\n".join(out)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(report())
