from typing import List, Tuple
import networkx as nx

from shapely.geometry import Point, LineString
from geopy.distance import geodesic

#Esta función lee un archivo con los puntos a visitar. En este momento lo lee desde 
    #data/points.txt pero en realidad se tiene que cargar desde la web
def load_points_to_visit(filepath: str) -> List[Tuple[int, float, float]]:
    
    points = []
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split()
            #debe contener 3 campos por linea (id, latitud, longitud)
            if len(parts) != 3:
                continue  
            node_id = int(parts[0])
            lat = float(parts[1])
            lon = float(parts[2])
            points.append((node_id, lat, lon))
    return points





#procesa cada nuevo nodo para validar si se debe insertar en el grafo
def process_points_into_graph(G: nx.Graph, points: List[Tuple[int, float, float]]
) -> List[int]:
    
    result_node_ids = []
    #recorre nodos nuevos (leídos en txt)
    for node_id, lat, lon in points:
        # Buscar nodo existente exacto (por coordenadas)
        existing = None
        #recorre los nodos que ya existen en el grafo
        for nid, data in G.nodes(data=True):
            if data.get("latitude") == lat and data.get("longitude") == lon:
                existing = nid
                break

        if existing is not None:
            result_node_ids.append(existing)
        else:
            # si el nodo no existe actualmente en el grafo, lo debe insertar
            new_id = insert_node_into_graph(G, node_id, lat, lon)
            result_node_ids.append(new_id)

    #retorno ids de todos los nodos
    return result_node_ids



#inserta nuevos nodos en el grafo, para eso busca la arista mas cercana y la divide en 2
def insert_node_into_graph(G: nx.Graph, new_id: int, lat: float, lon: float) -> int:
  
    new_point = Point(lat, lon)
    closest_edge = None
    min_distance = float("inf")

    # Buscar la arista más cercana (por distancia perpendicular)
    for u, v in G.edges():
        u_data = G.nodes[u]
        v_data = G.nodes[v]

        line = LineString([
            (u_data["latitude"], u_data["longitude"]),
            (v_data["latitude"], v_data["longitude"])
        ])
        distance = new_point.distance(line)

        if distance < min_distance:
            min_distance = distance
            closest_edge = (u, v)

    if closest_edge is None:
        raise ValueError("No edge found to insert point")

    u, v = closest_edge
    coord_u = (G.nodes[u]["latitude"], G.nodes[u]["longitude"])
    coord_v = (G.nodes[v]["latitude"], G.nodes[v]["longitude"])
    new_coord = (lat, lon)

    # se elimina la arista original (ya que se debe dividir en 2)
    G.remove_edge(u, v)

    # se inserta el nuevo nodo
    G.add_node(new_id, latitude=lat, longitude=lon)

    # Conectar los extremos de la anterior arista con el nuevo nodo 
    dist_u = geodesic(coord_u, new_coord).meters
    dist_v = geodesic(new_coord, coord_v).meters
    G.add_edge(u, new_id, weight=dist_u)
    G.add_edge(new_id, v, weight=dist_v)

    return new_id
