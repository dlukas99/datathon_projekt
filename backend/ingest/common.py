"""Shared helpers for data ingestion: polite downloads and the source manifest."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app.config import get_settings

MANIFEST_NAME = "manifest.json"
_last_request: dict[str, float] = {}


def raw_dir(*parts: str) -> Path:
    path = get_settings().raw_dir.joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def processed_dir() -> Path:
    path = get_settings().processed_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def http_client(timeout: float = 120.0) -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": get_settings().user_agent},
        timeout=timeout,
        follow_redirects=True,
    )


def _throttle(host: str, min_interval: float) -> None:
    last = _last_request.get(host)
    if last is not None:
        wait = min_interval - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
    _last_request[host] = time.monotonic()


def download(url: str, dest: Path, *, min_interval: float = 1.0, retries: int = 3) -> Path:
    """Download `url` to `dest` unless it already exists. Returns `dest`."""
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    host = httpx.URL(url).host
    for attempt in range(1, retries + 1):
        _throttle(host, min_interval)
        try:
            with http_client() as client, client.stream("GET", url) as response:
                response.raise_for_status()
                with tmp.open("wb") as fh:
                    for chunk in response.iter_bytes(1 << 20):
                        fh.write(chunk)
            tmp.replace(dest)
            return dest
        except httpx.HTTPError:
            if attempt == retries:
                raise
            time.sleep(2**attempt)
    return dest


def get_json(url: str, *, params: dict[str, Any] | None = None, min_interval: float = 1.0) -> Any:
    _throttle(httpx.URL(url).host, min_interval)
    with http_client() as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def file_date(path: Path) -> str:
    """Retrieval date of a downloaded file (its modification time), ISO 8601 UTC."""
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat(timespec="seconds")


def record_source(source_id: str, **meta: Any) -> None:
    """Store metadata of a processed source in data/processed/manifest.json.

    Expected keys: title, publisher, url, license, retrieved_at, and optionally
    data_date (reference date or year of the data) and notes.
    """
    path = processed_dir() / MANIFEST_NAME
    manifest: dict[str, Any] = {}
    if path.exists():
        manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest[source_id] = meta
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
