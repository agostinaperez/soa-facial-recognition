# Servicio para interactuar con SeaweedFS mediante la api

import os

import httpx

SEAWEED_MASTER = os.getenv("SEAWEED_MASTER", "http://localhost:9333")
SEAWEED_VOLUME = os.getenv("SEAWEED_VOLUME", "http://localhost:8080")

_TIMEOUT = 30


def upload_image(file_bytes: bytes, filename: str) -> str:
    with httpx.Client(timeout=_TIMEOUT) as client:
        # hace un get al master y obtiene file_id (fid) + volume URL
        assign = client.get(f"{SEAWEED_MASTER}/dir/assign")
        assign.raise_for_status()
        data = assign.json()
        file_id: str = data["fid"]

        endpoint = f"{SEAWEED_VOLUME}/{file_id}"
        upload = client.post(endpoint, files={"file": (filename, file_bytes)})
        upload.raise_for_status()
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
