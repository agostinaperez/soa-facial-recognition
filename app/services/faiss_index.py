import faiss
import numpy as np
import torch

# face_recognition siempre genera vectores de exactamente 128 números flotantes
DIMENSION = 128

# True si hay GPU NVIDIA disponible Y faiss-gpu está instalado
_USE_GPU = torch.cuda.is_available() and faiss.get_num_gpus() > 0


def build_index(vectors: list, person_ids: list):
    """Construye un índice FAISS en memoria a partir de los vectores dados.

    IndexFlatL2 realiza búsqueda exacta por distancia euclídea al cuadrado (L2²).
    No es aproximado: siempre encuentra el vecino real más cercano.
    Si hay GPU NVIDIA disponible y faiss-gpu está instalado, mueve el índice a GPU
    automáticamente. En caso contrario usa CPU sin cambios.

    Args:
        vectors: lista de embeddings (cada uno es una lista de 128 floats).
        person_ids: lista paralela de UUIDs. person_ids[i] es el dueño de vectors[i].

    Returns:
        Tupla (index, person_ids_list) donde person_ids_list[i] mapea la posición
        interna de FAISS al personId correspondiente.
    """
    index_cpu = faiss.IndexFlatL2(DIMENSION)

    if vectors:
        # FAISS requiere float32. Los vectores vienen de MySQL como float64 (Python nativo).
        matrix = np.array(vectors, dtype=np.float32)
        index_cpu.add(matrix)  # agrega todos los vectores de una sola vez (operación vectorizada)

    # Retornamos el índice Y la lista de personIds porque FAISS internamente
    # trabaja con enteros (posición 0, 1, 2...), no con UUIDs.
    # person_ids[i] nos dice a qué persona pertenece el vector en la posición i del índice.
    if _USE_GPU:
        res = faiss.StandardGpuResources()
        index = faiss.index_cpu_to_gpu(res, 0, index_cpu)  # mueve el índice a GPU 0
    else:
        index = index_cpu

    return index, list(person_ids)


def search(index, person_ids: list, query_vector: list, k: int = 1):
    """Busca los k vecinos más cercanos al query_vector dentro del índice.

    Args:
        index: índice FAISS construido con build_index (CPU o GPU).
        person_ids: lista de UUIDs paralela al índice (retornada por build_index).
        query_vector: embedding de la imagen consulta (128 floats).
        k: cantidad de vecinos a retornar (por defecto 1).

    Returns:
        Lista de tuplas (personId, distancia_l2_cuadrada) ordenadas de menor a mayor distancia.
        IMPORTANTE: la distancia retornada es L2², no la distancia euclídea directa.
        Para convertir a confidence usar: confidence = 1.0 - sqrt(distancia_l2_cuadrada).
    """
    # FAISS espera un array 2D: (cantidad_de_consultas, dimensión).
    # Como hacemos una sola consulta a la vez, el shape es (1, 128).
    query = np.array([query_vector], dtype=np.float32)

    distances, indices = index.search(query, k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        # FAISS retorna idx == -1 cuando el índice tiene menos vectores que k
        if idx == -1:
            continue
        results.append((person_ids[idx], float(dist)))  # tupla (personId, distancia_l2²)

    return results
