import io
import os
import pytest

import app.main as main  # <-- Importa el módulo donde están los endpoints
from app.main import app
from fastapi.testclient import TestClient

DATA_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "data")

@pytest.fixture
def client():
    return TestClient(app)


# --- Pruebas para /upload-graph ---
def test_upload_graph_extensión_invalida(client):
    fake_file = io.BytesIO(b"no importa")
    response = client.post(
        "/upload-graph",
        files={"file": ("points.txt", fake_file, "text/plain")}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Only .osm files are supported"


def test_upload_graph_ok(client, monkeypatch):
    # Cargamos un .osm real de prueba
    osm_path = os.path.join(DATA_DIR, "chapinero.osm")
    with open(osm_path, "rb") as f:
        content = f.read()
    fake_file = io.BytesIO(content)

    # Parcheamos la función que usa app.main
    monkeypatch.setattr(
        main, "load_graph_from_file",
        lambda f: {"nodes": 123, "edges": 456}
    )

    response = client.post(
        "/upload-graph",
        files={"file": ("chapinero.osm", fake_file, "application/xml")}
    )
    assert response.status_code == 200
    assert response.json() == {"nodes": 123, "edges": 456}


# --- Pruebas para /graph-data ---
def test_graph_data_success(client, monkeypatch):
    esperado = {"nodes": [1, 2, 3], "edges": []}
    monkeypatch.setattr(main, "get_graph_data", lambda: esperado)

    response = client.get("/graph-data")
    assert response.status_code == 200
    assert response.json() == esperado


def test_graph_data_error(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "get_graph_data",
        lambda: (_ for _ in ()).throw(Exception("fail"))
    )

    response = client.get("/graph-data")
    assert response.status_code == 400
    assert "fail" in response.json()["detail"]


# --- Fixture para TSP endpoints ---
@pytest.fixture(autouse=True)
def setup_tsp(monkeypatch):
    # Matriz simulada
    class FakeMatrix:
        distances = [[0, 1], [1, 0]]
        paths = [[[], [1]], [[0], []]]

    monkeypatch.setattr(main, "get_distance_matrix", lambda: FakeMatrix())
    monkeypatch.setattr(main, "get_selected_nodes", lambda: [10, 20])

    # Resultado simulado para los tres algoritmos
    class Resultado:
        algorithmName = "dummy"
        path = [0, 1]
        total_cost = 1.23
        execution_time = 0.004

    monkeypatch.setattr(main, "solve_tsp_brute_force", lambda d: Resultado())
    monkeypatch.setattr(main, "solve_tsp_greedy", lambda d: Resultado())
    monkeypatch.setattr(main, "solve_tsp_dynamic_programming", lambda d: Resultado())


def test_tsp_brute_force(client):
    r = client.get("/tsp/brute-force")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    # [0,1] → IDs [10,20]
    assert body["result"]["path"] == [10, 20]


def test_tsp_greedy(client):
    r = client.get("/tsp/greedy")
    assert r.status_code == 200
    assert r.json()["status"] == "success"


def test_tsp_dynamic(client):
    r = client.get("/tsp/dynamic")
    assert r.status_code == 200
    assert r.json()["status"] == "success"
