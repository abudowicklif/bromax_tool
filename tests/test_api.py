from fastapi.testclient import TestClient
from bromax.main import app

def test_dashboard_and_status():
    with TestClient(app) as client:
        dashboard = client.get("/")
        assert dashboard.status_code == 200
        assert "<title>BROMAX · Live research</title>" in dashboard.text
        assert "Digit distribution" in dashboard.text
        for hidden_section in (
            "Agent cross-examination",
            "Verifier decisions",
            "Historical walk-forward backtest",
            "Assumptions &amp; limitations",
            "Recent feed diagnostics",
            "Live digit stream",
        ):
            assert hidden_section not in dashboard.text
        r=client.get("/api/status")
        assert r.status_code == 200
        assert "analysis" in r.json()

def test_backtest_requires_data():
    with TestClient(app) as client:
        r=client.get("/api/backtest")
        assert r.status_code in (200,422)
