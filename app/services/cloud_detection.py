
import os
from io import BytesIO

from PIL import Image

AZURE_ENDPOINT = os.getenv("AZURE_FACE_ENDPOINT", "").rstrip("/")
AZURE_KEY = os.getenv("AZURE_FACE_KEY", "")

MIN_FACE_SIZE = 36

def enrich_face(image_bytes: bytes) -> dict | None:
    if not AZURE_ENDPOINT or not AZURE_KEY:
        return None

    try:
        import httpx
        #llamo a Azure Face API para detectar la cara y obtener atributos (edad, genero, etc)
        url = f"{AZURE_ENDPOINT}/face/v1.0/detect"
        params = {
            "returnFaceId": "false",
            "returnFaceLandmarks": "true",
            "returnFaceAttributes": "blur,exposure,glasses,headPose,mask,occlusion,qualityForRecognition",
            "recognitionModel": "recognition_04",
            "detectionModel": "detection_03",
        }
        headers = {
            "Ocp-Apim-Subscription-Key": AZURE_KEY,
            "Content-Type": "application/octet-stream",
        }
        resp = httpx.post(url, params=params, headers=headers, content=image_bytes, timeout=15)
        resp.raise_for_status()
        faces = resp.json()
        if not faces:
            return None
        face = faces[0]
        result = {
            "faceRectangle": face.get("faceRectangle"),
            "faceAttributes": face.get("faceAttributes"),
            "faceLandmarks": face.get("faceLandmarks"),
        }
        return result
    except Exception:
        return None


def crop_face(image_bytes: bytes, bbox: dict) -> bytes | None:
    try:
        img = Image.open(BytesIO(image_bytes))
        x1 = int(bbox["x1"])
        y1 = int(bbox["y1"])
        x2 = int(bbox["x2"])
        y2 = int(bbox["y2"])
        if x2 - x1 < MIN_FACE_SIZE or y2 - y1 < MIN_FACE_SIZE:
            return None
        crop = img.crop((x1, y1, x2, y2))
        buf = BytesIO()
        crop.save(buf, format="JPEG")
        return buf.getvalue()
    except Exception:
        return None
