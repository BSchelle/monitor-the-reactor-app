from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"greeting": "Monitor the Reactor API is running"}

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert "status" in json_data
    assert "modelloaded" in json_data
    assert "preprocessorloaded" in json_data

def test_predict():
    response = client.post(
        "/predict",
        json={"temperature": 100, "pressure": 5, "flowrate": 10, "vibration": 0.3, "threshold": 0.8}
    )
    assert response.status_code == 200
    data = response.json()
    assert "probability" in data
    assert 0.0 <= data["probability"] <= 1.0
    assert "alert" in data
