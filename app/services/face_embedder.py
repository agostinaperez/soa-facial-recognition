
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
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image is None:
        return None

    face_locs = face_recognition.face_locations(image)
    if not face_locs:
        return None

    fr = face_recognition.face_encodings(image, known_face_locations=[face_locs[0]])
    if not fr:
        return None

    return fr[0].tolist()
