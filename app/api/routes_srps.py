
# Servicio SRPS: Piedra, Papel o Tijera
# POST /rps/play — clasifica el gesto de la mano del usuario vía YOLO y
# resuelve una ronda contra una jugada aleatoria del servidor.

from fastapi import APIRouter, Depends, HTTPException

from schemas.dtos import RPSPlayRequest, RPSPlayResponse
from security import require_roles
from worker.celery_app import celery_app

router = APIRouter()


@router.post("/rps/play", response_model=RPSPlayResponse)
def rps_play_endpoint(
    body: RPSPlayRequest,
    _: dict = Depends(require_roles(["admin", "operator", "viewer"])),
) -> RPSPlayResponse:
    task = celery_app.send_task("worker.tasks.rps_play_task", args=[body.image])
    result = task.get(timeout=30)

    if "error" in result:
        raise HTTPException(status_code=422, detail=result["detail"])

    return RPSPlayResponse(**result)
