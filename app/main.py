from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import traceback


from app.services.graph_loader import get_graph
from app.services.graph_loader import get_graph_data
from app.services.graph_loader import load_graph_from_file
from app.services.process_nodes import process_points_into_graph

from app.services.distance_matrix import build_distance_matrix_with_paths

from app.services.tsp_solver import solve_tsp_brute_force
from app.services.tsp_solver import solve_tsp_greedy
from app.utils.path_utils import map_path_indices_to_ids, reconstruct_full_path

from app.services.tsp_solver import solve_tsp_dynamic_programming

from app.services.process_nodes import load_points_from_uploaded_file
from app.services.graph_loader import get_graph

from app.services.process_nodes import get_selected_nodes
from app.services.distance_matrix import build_distance_matrix_with_paths,get_distance_matrix, set_distance_matrix




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




@app.post("/upload-points")
async def upload_points(file: UploadFile = File(...)):
    try:
        G = get_graph()
        node_ids = load_points_from_uploaded_file(file.file, G)
        return {
            "status": "success",
            "numPoints": len(node_ids),
            "nodeIds": node_ids
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")






@app.get("/build-matrix")
def build_matrix():
    try:
        G = get_graph()
        node_ids = get_selected_nodes()

        if not node_ids or len(node_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 points are required.")

        matrix = build_distance_matrix_with_paths(G, node_ids)
        set_distance_matrix(matrix)

        return {
            "status": "success",
            "numPoints": len(node_ids)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def limit_nodes_and_get_mapping(distance_matrix: List[List[float]], node_ids: List, algorithm: str, start_index: int = 0):
    """
    Limita nodos según el algoritmo y retorna la matriz limitada y el mapeo de IDs.
    """
    n = len(distance_matrix)
    
    if algorithm.lower() in ["brute_force", "fuerza_bruta", "brute"]:
        max_nodes = 12
    elif algorithm.lower() in ["dynamic_programming", "programacion_dinamica", "held_karp", "dp"]:
        max_nodes = 20
    else:  # Greedy u otros algoritmos
        max_nodes = n  # Sin límite para Greedy
    
    if n <= max_nodes:
        return distance_matrix, node_ids, start_index
    
    # Seleccionar los primeros max_nodes nodos
    selected_indices = list(range(max_nodes))
    
    # Si start_index no está en los primeros max_nodes, intercambiarlo con el primero
    if start_index >= max_nodes:
        selected_indices[0] = start_index
        selected_indices = sorted(selected_indices)
        adjusted_start_index = selected_indices.index(start_index)
    else:
        adjusted_start_index = start_index
    
    # Crear la nueva matriz de distancias limitada
    limited_matrix = []
    for i in selected_indices:
        row = []
        for j in selected_indices:
            row.append(distance_matrix[i][j])
        limited_matrix.append(row)
    
    # Crear la lista limitada de node_ids
    limited_node_ids = [node_ids[i] for i in selected_indices]
    
    print(f"Algoritmo: {algorithm}")
    print(f"Nodos originales: {n}, Nodos limitados: {len(limited_matrix)}")
    print(f"Índices seleccionados: {selected_indices}")
    
    return limited_matrix, limited_node_ids, adjusted_start_index


# Endpoints modificados para FastAPI:

#solución de TSP para programación dinámica
@app.get("/tsp/dynamic")
def run_held_karp():
    try:
        matrix = get_distance_matrix()
        node_ids = get_selected_nodes()

        if not matrix or not node_ids:
            raise HTTPException(status_code=400, detail="Missing matrix or selected nodes.")

        # Limitar nodos para programación dinámica (máximo 20)
        limited_matrix, limited_node_ids, adjusted_start_index = limit_nodes_and_get_mapping(
            matrix.distances, node_ids, "dynamic_programming", start_index=0
        )

        result = solve_tsp_dynamic_programming(limited_matrix, adjusted_start_index)

        real_path = map_path_indices_to_ids(result.path, limited_node_ids)
        full_path = reconstruct_full_path(result.path, matrix.paths)

        return {
            "status": "success",
            "result": {
                "algorithmName": result.algorithmName,
                "path": real_path,  # esto para las estadísticas
                "total_cost": result.total_cost,
                "execution_time": result.execution_time,
                "nodes_used": len(limited_node_ids),  # Información adicional
                "total_nodes_available": len(node_ids)
            },
            "fullPath": full_path  # esto se dibuja en el mapa (con nodos intermedios)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


#fuerza bruta
@app.get("/tsp/brute-force")
def run_brute_force():
    try:
        matrix = get_distance_matrix()
        node_ids = get_selected_nodes()

        if not matrix or not node_ids:
            raise HTTPException(status_code=400, detail="Missing matrix or selected nodes.")

        # Limitar nodos para fuerza bruta (máximo 12)
        limited_matrix, limited_node_ids, adjusted_start_index = limit_nodes_and_get_mapping(
            matrix.distances, node_ids, "brute_force", start_index=0
        )

        result = solve_tsp_brute_force(limited_matrix, adjusted_start_index)

        real_path = map_path_indices_to_ids(result.path, limited_node_ids)
        full_path = reconstruct_full_path(result.path, matrix.paths)

        return {
            "status": "success",
            "result": {
                "algorithmName": result.algorithmName,
                "path": real_path,
                "total_cost": result.total_cost,
                "execution_time": result.execution_time,
                "nodes_used": len(limited_node_ids),  # Información adicional
                "total_nodes_available": len(node_ids)
            },
            "fullPath": full_path
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Greedy (vecino más cercano)
@app.get("/tsp/greedy")
def run_greedy():
    try:
        matrix = get_distance_matrix()
        node_ids = get_selected_nodes()

        if not matrix or not node_ids:
            raise HTTPException(status_code=400, detail="Missing matrix or selected nodes.")

        # Greedy puede manejar todos los nodos, pero usamos la misma función por consistencia
        limited_matrix, limited_node_ids, adjusted_start_index = limit_nodes_and_get_mapping(
            matrix.distances, node_ids, "greedy", start_index=0
        )

        result = solve_tsp_greedy(limited_matrix, adjusted_start_index)

        real_path = map_path_indices_to_ids(result.path, limited_node_ids)
        full_path = reconstruct_full_path(result.path, matrix.paths)

        return {
            "status": "success",
            "result": {
                "algorithmName": result.algorithmName,
                "path": real_path,  # esto para las estadísticas
                "total_cost": result.total_cost,
                "execution_time": result.execution_time,
                "nodes_used": len(limited_node_ids),  # Información adicional
                "total_nodes_available": len(node_ids)
            },
            "fullPath": full_path  # esto se dibuja en el mapa (con nodos intermedios)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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
