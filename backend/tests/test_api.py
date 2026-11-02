from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_openapi_is_published() -> None:
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert {"/api/report", "/api/geocode", "/api/sources"} <= set(paths)


def test_report_rejects_points_outside_croatia() -> None:
    response = client.get("/api/report", params={"lat": 48.2, "lon": 16.37})
    assert response.status_code == 422
    assert response.json()["detail"] == "Lokacija nije u Hrvatskoj."


def test_geocode_requires_query() -> None:
    assert client.get("/api/geocode", params={"q": "a"}).status_code == 422
