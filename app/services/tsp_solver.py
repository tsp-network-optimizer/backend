from typing import List
from itertools import permutations
import time
from app.models.tsp_result import TSPResult

def solve_tsp_brute_force(distance_matrix: List[List[float]], start_index: int = 0) -> TSPResult:
    n = len(distance_matrix)
    nodes = list(range(n))
    nodes.remove(start_index)

    best_path = []
    min_cost = float('inf')

    start_time = time.time()

    #para generar todas las posibles combinaciones en las que se puede visitar los nodos
    for perm in permutations(nodes):
        path = [start_index] + list(perm) + [start_index]
        cost = 0.0

        #suma costo total del camino que se está evaluando
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            cost += distance_matrix[a][b]

        #si es la mejor en terminos de distancia, actualiza
        if cost < min_cost:
            min_cost = cost
            best_path = path

    end_time = time.time()
    #tiempo total que demoró el algoritmo
    execution_time = end_time - start_time

    return TSPResult(path=best_path, total_cost=min_cost, execution_time=execution_time, algorithmName = "Fuerza bruta")
  