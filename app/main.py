from fastapi import FastAPI

from app.services.graph_loader import get_graph
from app.services.process_nodes import load_points_to_visit, process_points_into_graph

from app.services.distance_matrix import build_distance_matrix_with_paths

app = FastAPI()

@app.get("/prueba")
def prueba():
    return {"message": "prueba"}




def main():
    # simular grafo
    G = get_graph()
    print(f"Grafo inicial: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")

    # cargar los puntos desde .txt
    file_path = "data/points.txt" 
    points = load_points_to_visit(file_path)
    print(f"Leídos {len(points)} puntos desde archivo.")

    # procesar nuevos nodos leídos
    final_node_ids = process_points_into_graph(G, points)
    print("Nodos a visitar (IDs en el grafo):", final_node_ids)

    #nuevo estado del grafo, con las modificaciones
    print(f"Grafo actualizado: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")





    # crear matriz de distancias según los nodos que se quieren visitar
    result = build_distance_matrix_with_paths(G, final_node_ids)

    # imprimir matriz de distancias
    print("\nMatriz de distancias:")
    for row in result.distances:
        print(["{:.1f}".format(val) if val != float("inf") else "∞" for val in row])

    # imprimir caminos desde nodo i hasta nodo j
    print("\nMatriz de caminos reales:")
    for i in range(len(result.paths)):
        for j in range(len(result.paths)):
            if i != j:
                print(f"De {final_node_ids[i]} a {final_node_ids[j]}: {result.paths[i][j]}")

if __name__ == "__main__":
    main()
