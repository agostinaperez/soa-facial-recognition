
import json

import cv2
import face_recognition
import numpy as np


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def generate_face_embedding(image_bytes: bytes) -> list[float] | None:
    # Detecta la primer cara en la imagen y devuelve su embedding de 128 floats
    # el codigo se sacó del código del profe
    np_arr = np.frombuffer(image_bytes, np.uint8)
    if np_arr.size == 0:
        return None
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        return None
    
    height, width = image.shape[:2]

    MIN_WIDTH = 200
    MIN_HEIGHT = 200

    if width < MIN_WIDTH or height < MIN_HEIGHT:
        raise ValueError(
            f"Resolución insuficiente ({width}x{height})"
        )

    face_locs = face_recognition.face_locations(image)

    # No hay caras
    if len(face_locs) == 0:
        return None

    # Hay más de una cara
    if len(face_locs) > 1:
        raise ValueError("La imagen debe contener un único rostro")

    fr = face_recognition.face_encodings(
        image,
        known_face_locations=face_locs
    )

    if not fr:
        return None

    return fr[0].tolist()
