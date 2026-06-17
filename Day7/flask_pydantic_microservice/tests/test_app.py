import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "success"


def test_create_prediction_success(client):
    payload = {
        "name": "Vishal",
        "age": 25,
        "salary": 60000
    }

    response = client.post("/predictions", json=payload)

    assert response.status_code == 201
    assert "prediction_id" in response.json
    assert response.json["result"] == "Approved"


def test_create_prediction_invalid_payload(client):
    payload = {
        "name": "V",
        "age": -5,
        "salary": 0
    }

    response = client.post("/predictions", json=payload)

    assert response.status_code == 422
    assert response.json["error"] == "Validation Error"


def test_get_prediction_not_found(client):
    response = client.get("/predictions/invalid-id")

    assert response.status_code == 404
    assert response.json["error"] == "Not Found"