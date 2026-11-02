"""Raster sources: JRC flood depth, EEA annual air quality, ESA WorldCover.

Europe-wide rasters are clipped to Croatia and stored as tiled, compressed
GeoTIFFs in data/processed/. WorldCover tiles are already cloud-optimised and
are copied unchanged.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds

from ingest.common import download, file_date, processed_dir, raw_dir, record_source

# Croatia with a small margin, lon/lat.
CROATIA_BOUNDS = (13.3, 42.3, 19.5, 46.6)

JRC_BASE = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard"
JRC_RETURN_PERIODS = (10, 100, 500)

EEA_YEAR = 2024
EEA_AIR = {
    "pm25": "https://sdi.eea.europa.eu/webdav/datastore/public/"
    "eea_r_3035_1_km_aq-interpolated-pm25_p_2024_v01_r00/pm25_avg_24.tif",
    "no2": "https://sdi.eea.europa.eu/webdav/datastore/public/"
    "eea_r_3035_1_km_aq-interpolated-no2_p_2024_v01_r00/no2_avg_24.tif",
}
EEA_RECORDS = {
    "pm25": "https://sdi.eea.europa.eu/catalogue/srv/api/records/c3db03e4-82e9-4a40-acb1-a5bd15f11f8c",
    "no2": "https://sdi.eea.europa.eu/catalogue/srv/api/records/4c6361bd-cfd4-48de-9b4b-101cfb37f1f0",
}

WORLDCOVER_URL = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
    "ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
)
WORLDCOVER_TILES = ("N42E012", "N42E015", "N42E018", "N45E012", "N45E015", "N45E018")


def clip_to_croatia(src_path: Path, dst_path: Path) -> None:
    with rasterio.open(src_path) as src:
        bounds = transform_bounds("EPSG:4326", src.crs, *CROATIA_BOUNDS)
        window = from_bounds(*bounds, transform=src.transform).round_offsets().round_lengths()
        data = src.read(1, window=window)
        profile = src.profile.copy()
        profile.update(
            width=window.width,
            height=window.height,
            transform=src.window_transform(window),
            tiled=True,
            blockxsize=256,
            blockysize=256,
            compress="deflate",
            predictor=3 if data.dtype.kind == "f" else 2,
            BIGTIFF="IF_SAFER",
        )
    tmp = dst_path.with_suffix(".tmp.tif")
    with rasterio.open(tmp, "w", **profile) as dst:
        dst.write(data, 1)
    tmp.replace(dst_path)


def flood() -> None:
    out = processed_dir()
    last = None
    for rp in JRC_RETURN_PERIODS:
        name = f"Europe_RP{rp}_filled_depth.tif"
        src = download(f"{JRC_BASE}/{name}", raw_dir("jrc_flood") / name)
        dst = out / f"flood_rp{rp}.tif"
        if not dst.exists():
            clip_to_croatia(src, dst)
        last = src
    assert last is not None
    record_source(
        "jrc_flood",
        title="Karte opasnosti od riječnih poplava za Europu (CEMS-EFAS), v3.1.1",
        publisher="Europska komisija, Zajednički istraživački centar (JRC)",
        url="https://data.jrc.ec.europa.eu/dataset/1d128b6c-a4ee-4858-9e34-6210707f3c81",
        license="ODbL 1.0 prema katalogu JRC-a; CC BY 4.0 prema copyright.txt u mapi preuzimanja",
        retrieved_at=file_date(last),
        data_date="verzija 3.1.1 od 5. 3. 2026.",
    )


def air() -> None:
    out = processed_dir()
    for pollutant, url in EEA_AIR.items():
        src = download(url, raw_dir("eea_air") / Path(url).name)
        dst = out / f"air_{pollutant}_{EEA_YEAR}.tif"
        if not dst.exists():
            clip_to_croatia(src, dst)
        record_source(
            f"eea_{pollutant}",
            title=(
                f"Interpolirana karta kvalitete zraka, godišnji prosjek "
                f"{'PM2,5' if pollutant == 'pm25' else 'NO2'} za {EEA_YEAR}., 1 km"
            ),
            publisher="Europska agencija za okoliš (EEA)",
            url=EEA_RECORDS[pollutant],
            license="CC BY 4.0",
            retrieved_at=file_date(src),
            data_date=str(EEA_YEAR),
        )


def worldcover() -> None:
    out = processed_dir() / "worldcover"
    out.mkdir(parents=True, exist_ok=True)
    last = None
    for tile in WORLDCOVER_TILES:
        url = WORLDCOVER_URL.format(tile=tile)
        src = download(url, raw_dir("worldcover") / Path(url).name)
        dst = out / src.name
        if not dst.exists():
            shutil.copyfile(src, dst)
        last = src
    assert last is not None
    record_source(
        "worldcover",
        title="ESA WorldCover 10 m 2021 v200",
        publisher="Europska svemirska agencija (ESA), konzorcij WorldCover",
        url="https://doi.org/10.5281/zenodo.7254221",
        license="CC BY 4.0",
        retrieved_at=file_date(last),
        data_date="2021",
        notes="© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data "
        "(2021) processed by ESA WorldCover consortium",
    )


def run() -> None:
    air()
    worldcover()
    flood()


if __name__ == "__main__":
    run()
