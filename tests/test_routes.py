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

    monkeypatch.setattr(main, "solve_tsp_brute_force", lambda d, i: Resultado())
    monkeypatch.setattr(main, "solve_tsp_greedy", lambda d, i: Resultado())
    monkeypatch.setattr(main, "solve_tsp_dynamic_programming", lambda d, i: Resultado())
    monkeypatch.setattr(main, "reconstruct_full_path", lambda path, paths: [])


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

@pytest.mark.parametrize("returned_nodes", [
    [],                # 0 nodos
    [42],              # 1 nodo
    [1, 2, 3, 4, 5],   # 5 nodos
])
def test_upload_points_varias_cantidades(client, monkeypatch, returned_nodes):

    monkeypatch.setattr(main, "get_graph", lambda: None)
    monkeypatch.setattr(
        main,
        "load_points_from_uploaded_file",
        lambda f, G: returned_nodes
    )

    response = client.post(
        "/upload-points",
        files={"file": ("dummy.txt", io.BytesIO(b""), "text/plain")}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["numPoints"] == len(returned_nodes)
    assert body["nodeIds"] == returned_nodes



@pytest.mark.parametrize("selected_nodes, expected_status", [
    ([],  500),   # < 2 nodos → 400
    ([1], 500),   # < 2 nodos → 400
    ([1,2], 200), # 2 nodos → 200
    ([1,2,3], 200)# > 2 nodos → 200
])
def test_build_matrix_varias_cantidades(client, monkeypatch, selected_nodes, expected_status):
    monkeypatch.setattr(main, "get_graph", lambda: None)
    monkeypatch.setattr(main, "get_selected_nodes", lambda: selected_nodes)

    if expected_status == 200:
        monkeypatch.setattr(main, "build_distance_matrix_with_paths", lambda G, ns: "fake-matrix")
        monkeypatch.setattr(main, "set_distance_matrix", lambda m: None)

    response = client.get("/build-matrix")
    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["status"] == "success"
        assert response.json()["numPoints"] == len(selected_nodes)
    else:
        # Como el detalle se convierte en "400: At least 2 points are required."
        assert "At least 2 points are required" in response.json()["detail"]


# --- TSP para 2,3 y 4 nodos en los 3 endpoints ---
@pytest.mark.parametrize("nodes, fake_path, expected_mapped", [
    ([10,20],      [0,1],       [10,20]),        
    ([3,5,7],      [2,0,1],     [7,3,5]),        
    ([100,200,300,400], [3,1,2,0], [400,200,300,100]),
])
@pytest.mark.parametrize("endpoint", ["/tsp/brute-force", "/tsp/greedy", "/tsp/dynamic"])
def test_tsp_varias_cantidades(client, monkeypatch, nodes, fake_path, expected_mapped, endpoint):
    class FakeMatrix:
        distances = []
        paths = []
    monkeypatch.setattr(main, "get_distance_matrix", lambda: FakeMatrix())
    monkeypatch.setattr(main, "get_selected_nodes", lambda: nodes)

    class Resultado:
        algorithmName = "dummy"
        path = fake_path
        total_cost = 99.9
        execution_time = 0.123

    if "brute-force" in endpoint:
        monkeypatch.setattr(main, "solve_tsp_brute_force", lambda d, i: Resultado())
    elif "greedy" in endpoint:
        monkeypatch.setattr(main, "solve_tsp_greedy", lambda d, i: Resultado())
    else:
        monkeypatch.setattr(main, "solve_tsp_dynamic_programming", lambda d, i: Resultado())


    r = client.get(endpoint)
    assert r.status_code == 200
    assert r.json()["status"] == "success"
    assert r.json()["result"]["path"] == expected_mapped