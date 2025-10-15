try:
    from fastapi.testclient import TestClient
    from part2.streaming_app import app
except Exception:  # Dependencies may be missing in fresh environments
    import pytest
    pytest.skip(
        "Skipping FastAPI app tests: dependencies not installed",
        allow_module_level=True,
    )


def test_healthz_ok():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.text.strip() == "ok"


def test_index_serves_html():
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    # Minimal sanity checks on the inline HTML UI
    assert "ADK Streaming" in r.text or "<html" in r.text.lower()
