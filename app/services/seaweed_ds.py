# Servicio para interactuar con SeaweedFS mediante la api

import os

import httpx

SEAWEED_MASTER = os.getenv("SEAWEED_MASTER", "http://localhost:9333")
SEAWEED_VOLUME = os.getenv("SEAWEED_VOLUME", "http://localhost:8080")

_TIMEOUT = 30


def upload_image(file_bytes: bytes, filename: str) -> str:
    """Sube un archivo binario al sistema de almacenamiento distribuido SeaweedFS.

    Esta función implementa el flujo de guardado en dos pasos requerido por la 
    arquitectura descentralizada de SeaweedFS:
    1. Consulta al componente Master para obtener una asignación de volumen y un ID único.
    2. Realiza el upload real del contenido binario hacia el Volume Server asignado.

    Args:
        file_bytes (bytes): Contenido en formato binario (bytes) de la imagen a subir.
        filename (str): Nombre original del archivo (útil para auditoría o extensiones).

    Returns:
        str: Identificador único del archivo en SeaweedFS (`file_id` o `fid`), necesario
             para persistir en MySQL y consultar la imagen posteriormente.

    Raises:
        httpx.HTTPStatusError: Si el Master no responde correctamente o si el Volume Server
                              falla al escribir el archivo físicamente (ej. disco lleno).
        httpx.RequestError: Si ocurren fallos de red en la conectividad entre contenedores.
    """
    with httpx.Client(timeout=_TIMEOUT) as client:
        
        # Solicitar asignación de ID y Servidor de Volumen al Master
        assign = client.get(f"{SEAWEED_MASTER}/dir/assign")
        assign.raise_for_status() # Detiene la ejecución si el Master responde con error (4xx/5xx)
        data = assign.json()
        file_id: str = data["fid"]
        public_url: str = data.get("publicUrl", data.get("url", ""))
        
        # Resolución dinámica del endpoint del servidor de volumen destino
        endpoint = (
            f"http://{public_url}/{file_id}"
            if public_url
            else f"{SEAWEED_VOLUME}/{file_id}"
        )
        
        # Sube el archivo al servidor de volumen.
        upload = client.post(endpoint, content=file_bytes)
        upload.raise_for_status() # detiene si hay errores
    # Retorna el file_id (identificador único en SeaweedFS).
    return file_id


def get_image(file_id: str) -> bytes:

    # Descarga una imagen desde SeaweedFS por su file_id.
    # GET /<file_id> al volume server.
    # Lanza HTTPStatusError si el archivo no existe (404).
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(f"{SEAWEED_VOLUME}/{file_id}")
        resp.raise_for_status()
        return resp.content
