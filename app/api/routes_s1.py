from fastapi import APIRouter, Depends

from security import require_roles
from services.yolo_core import get_available_models

router = APIRouter()


@router.get("/models")
def list_models(
    _: dict = Depends(require_roles(["admin", "operator", "viewer"])),
) -> list[str]:
    return get_available_models()
