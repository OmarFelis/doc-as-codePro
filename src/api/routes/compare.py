"""Compare route — POST /api/v1/compare."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.analyzers import diff_analyzer
from src.db.session import get_session
from src.db import repository
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class CompareRequest(BaseModel):
    microservice: str
    base_env: str = "QA"
    target_env: str = "DEV"


@router.post("/compare", tags=["Analysis"])
async def compare_environments(request: CompareRequest):
    """
    Compara las unidades lógicas de un microservicio entre dos entornos.

    Busca en quality_audits por entity_name + runtime_env para cada entorno
    y retorna las diferencias (added, removed, changed).
    """
    session = get_session()
    try:
        base_parent = repository.get_by_name_and_env(
            session, request.microservice, request.base_env
        )
        target_parent = repository.get_by_name_and_env(
            session, request.microservice, request.target_env
        )

        if not base_parent:
            raise HTTPException(
                status_code=404,
                detail=f"Microservicio '{request.microservice}' no encontrado en entorno '{request.base_env}'",
            )
        if not target_parent:
            raise HTTPException(
                status_code=404,
                detail=f"Microservicio '{request.microservice}' no encontrado en entorno '{request.target_env}'",
            )

        base_units = repository.get_by_parent(session, base_parent.id)
        target_units = repository.get_by_parent(session, target_parent.id)

        result = diff_analyzer.compare(base_units, target_units)

        logger.info(
            "diff_completed",
            microservice=request.microservice,
            base_env=request.base_env,
            target_env=request.target_env,
            summary=result["summary"],
        )

        return {
            "microservice": request.microservice,
            "base_env": request.base_env,
            "target_env": request.target_env,
            **result,
        }
    finally:
        session.close()
