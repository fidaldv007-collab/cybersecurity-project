from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "DevSecOps demo application is running"
    }


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cnapp_api():
    response = client.get("/api/cnapp")

    assert response.status_code == 200

    data = response.json()
    assert "sbom" in data
    assert "vulnerabilities" in data
    assert "ai_triage" in data
    assert "signature_verification" in data

    assert data["ai_triage"]["status"] in {"available", "unknown"}
    assert data["signature_verification"]["status"] in {
        "verified", "unknown"
    }

    triage = data["ai_triage"]
    if triage["status"] == "available":
        assert triage["method"] == "rule-based"
        assert isinstance(triage["findings"], list)
        assert triage["count"] == len(triage["findings"])
        assert triage["disclaimer"]


def test_dashboard():
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "CNAPP Security Dashboard" in response.text
    assert "Security Triage Findings" in response.text
    assert "/api/cnapp" in response.text
