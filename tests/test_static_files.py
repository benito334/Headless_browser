import os
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def setup_module(module):
    """Seed test files inside data directory so that /static can serve them."""
    data_dir = os.getenv("DATA_DIR", "./data")
    instagram_dir = os.path.join(data_dir, "instagram")
    os.makedirs(instagram_dir, exist_ok=True)
    with open(os.path.join(instagram_dir, "test.txt"), "w", encoding="utf-8") as f:
        f.write("hello world")
    with open(os.path.join(instagram_dir, "test.json"), "w", encoding="utf-8") as f:
        f.write('{"msg":"test"}')


def test_static_txt_served():
    r = client.get("/static/instagram/test.txt")
    assert r.status_code == 200
    assert "hello world" in r.text


def test_static_json_served():
    r = client.get("/static/instagram/test.json")
    assert r.status_code == 200
    assert r.json()["msg"] == "test"
