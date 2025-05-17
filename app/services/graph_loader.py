import networkx as nx #para grafos
import random
from geopy.distance import geodesic #para distancias


import osmnx as ox #para cargar archivo OSM en el grafo

# variable para el grafo, al inicio es nulo
_loaded_graph: nx.Graph | None = None


def get_graph() -> nx.Graph:
    return load_graph()



#carga datos al grafo usando archivo OSM en data/chapinero.osm
def load_graph() -> nx.Graph:
    global _loaded_graph

    #si ya está cargado lo retorna
    if _loaded_graph is not None:
        return _loaded_graph

    filepath = "data/chapinero.osm" 

    # carga el grafo según la ruta
    G = ox.graph_from_xml(filepath, simplify=True)


    # se convierte a grafo no dirigido
    if G.is_directed():
        G = G.to_undirected()

    # Asegurar lat/lon en cada nodo
    for node_id, data in G.nodes(data=True):
        data["latitude"] = data.get("y")
        data["longitude"] = data.get("x")

    # Calcular peso de la arista entre nodos (se usa distancia geodésica) 
    for u, v, data in G.edges(data=True):
        node_1 = G.nodes[u]
        node_2 = G.nodes[v]

        coord_1 = (node_1["latitude"], node_1["longitude"])
        coord_2 = (node_2["latitude"], node_2["longitude"])

        dist = geodesic(coord_1, coord_2).meters
        data["weight"] = dist

    _loaded_graph = G
    return G