from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import traceback


from app.services.graph_loader import get_graph
from app.services.graph_loader import get_graph_data
from app.services.graph_loader import load_graph_from_file
from app.services.process_nodes import load_points_to_visit, process_points_into_graph

from app.services.distance_matrix import build_distance_matrix_with_paths

from app.services.tsp_solver import solve_tsp_brute_force
from app.utils.path_utils import map_path_indices_to_ids, reconstruct_full_path

from app.services.tsp_solver import solve_tsp_dynamic_programming




app = FastAPI()
#para que se puedan hacer peticiones al API desde el front
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload-graph")
async def upload_graph(file: UploadFile = File(...)):
    if not file.filename.endswith(".osm"):
        raise HTTPException(status_code=400, detail="Only .osm files are supported")

    try:
        result = load_graph_from_file(file.file)
        return result
    except Exception as e:
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail=f"Error loading graph: {str(e)}")



@app.get("/graph-data")
def graph_data():
    try:
        return get_graph_data()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))





def main():
    # # simular grafo
    # G = get_graph()
    # print(f"Grafo inicial: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")

    # # cargar los puntos desde .txt
    # file_path = "data/points.txt" 
    # points = load_points_to_visit(file_path)
    # print(f"Leidos {len(points)} puntos desde archivo.")

    # # procesar nuevos nodos leídos
    # final_node_ids = process_points_into_graph(G, points)
    # print("Nodos a visitar (IDs en el grafo):", final_node_ids)

    # #nuevo estado del grafo, con las modificaciones
    # print(f"Grafo actualizado: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")





    # crear matriz de distancias según los nodos que se quieren visitar
    result_matrix = build_distance_matrix_with_paths(G, final_node_ids)

    # # imprimir matriz de distancias
    # print("\nMatriz de distancias:")
    # for row in result_matrix.distances:
    #     print(["{:.1f}".format(val) if val != float("inf") else "∞" for val in row])

    # # imprimir caminos desde nodo i hasta nodo j
    # print("\nMatriz de caminos reales:")
    # for i in range(len(result_matrix.paths)):
    #     for j in range(len(result_matrix.paths)):
    #         if i != j:
    #             print(f"De {final_node_ids[i]} a {final_node_ids[j]}: {result_matrix.paths[i][j]}")



    

    #ejecuta TSP por fuerza bruta
    # result_brute_force = solve_tsp_brute_force(result_matrix.distances)

    # resultados
    # print("\nNombre del algoritmo usado:")
    # print(result_brute_force.algorithmName)
    # print("\nRuta optima por fuerza bruta (indices en matriz):")
    # print(result_brute_force.path)
    # print(f"Costo total: {result_brute_force.total_cost:.2f} metros")
    # print(f"Tiempo de ejecucion: {result_brute_force.execution_time:.4f} segundos")

    # # pasar de los ids del arreglo a ids reales del grafo
    # id_path = map_path_indices_to_ids(result_brute_force.path, final_node_ids)
    # print("\nRuta como IDs reales:")
    # print(id_path)

    # # reconstruir ruta completa en el grafo (para tener todos los nodos intermedios por los que se pasa)
    # full_real_path = reconstruct_full_path(result_brute_force.path, result_matrix.paths)
    # print("\nRuta completa con nodos intermedios incluidos:")
    # print(full_real_path)




    # # Ejecutar el algoritmo de programación dinámica (Held-Karp)
    # result_dynamic = solve_tsp_dynamic_programming(result_matrix.distances)

    # print("\nNombre del algoritmo usado:")
    # print(result_dynamic.algorithmName)
    # print("\nRuta optima por programacion dinamica (indices en matriz):")
    # print(result_dynamic.path)
    # print(f"Costo total: {result_dynamic.total_cost:.2f} metros")
    # print(f"Tiempo de ejecucion: {result_dynamic.execution_time:.4f} segundos")

    # # Convertir índices a IDs reales
    # id_path_dynamic = map_path_indices_to_ids(result_dynamic.path, final_node_ids)
    # print("\nRuta como IDs reales:")
    # print(id_path_dynamic)

    # # Reconstruir ruta completa con nodos intermedios
    # full_real_path_dynamic = reconstruct_full_path(result_dynamic.path, result_matrix.paths)
    # print("\nRuta completa con nodos intermedios incluidos:")
    # print(full_real_path_dynamic)



    


if __name__ == "__main__":
    main()
