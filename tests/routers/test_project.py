from fastapi.testclient import TestClient

from bookcast.entities import Project
from bookcast.main import app

client = TestClient(app)


def test_index():
    response = client.get("/api/v1/projects/")
    assert response.status_code == 200

    resp = response.json()
    assert isinstance(resp, list)
    assert Project(**resp[0])


def test_show():
    response = client.get("/api/v1/projects/1")
    assert response.status_code == 200

    resp = response.json()
    assert Project(**resp)
