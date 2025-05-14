import networkx as nx #para grafos
import random
from geopy.distance import geodesic #para distancias

# variable para el grafo, al inicio es nulo
_loaded_graph: nx.Graph | None = None


def get_graph() -> nx.Graph:
    return load_graph()



#simula la creación del grafo, dado que aún no hay archivo específico para realizar lectura
def load_graph() -> nx.Graph:
    global _loaded_graph

    if _loaded_graph is not None:
        # si ya está cargado lo retorna
        return _loaded_graph  

    G = nx.Graph()

    # coordenadas de Bogotá para simular
    base_lat = 4.65
    base_lng = -74.1

    # Crea 20 nodos aleatorios
    for i in range(20):
        lat = base_lat + random.uniform(-0.03, 0.03)
        lng = base_lng + random.uniform(-0.03, 0.03)
        G.add_node(i, latitude=lat, longitude=lng)

    # Conectar cada nodo con sus 3 más cercanos (por distancia geodésica)
    nodes = list(G.nodes(data=True))
    for i, (id_a, data_a) in enumerate(nodes):
        coord_a = (data_a["latitude"], data_a["longitude"])
        distances = []

        for j, (id_b, data_b) in enumerate(nodes):
            if id_a == id_b:
                continue
            coord_b = (data_b["latitude"], data_b["longitude"])
            dist = geodesic(coord_a, coord_b).meters
            distances.append((id_b, dist))

        distances.sort(key=lambda x: x[1])
        closest = distances[:3]

        for target_id, dist in closest:
            if not G.has_edge(id_a, target_id):
                G.add_edge(id_a, target_id, weight=dist)

    _loaded_graph = G
    return G

